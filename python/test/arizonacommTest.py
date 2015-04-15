#! /usr/bin/env python
"""
Stork Project (http://www.cs.arizona.edu/stork/)
Module: arizonacommTest.py
Description:   test module for arizonacomm.py

Notes:
   See arizonacomm.py for more details.
"""

import arizonacomm as commlib
import arizonaunittest as unittestlib
import os,sys,time,socket,random
from threading import Thread

class async_run(Thread):
        def __init__(self,method,arg1=None,arg2=None,arg3=None,arg4=None):
                self.method=method
                self.arg1,self.arg2,self.arg3,self.arg4=arg1,arg2,arg3,arg4
                self.ret=None
                self.done=False
                self.exception=None
                Thread.__init__(self)
                self.start()
        def run(self):
                self.done=False
                arg1,arg2,arg3,arg4=self.arg1,self.arg2,self.arg3,self.arg4 
                #commented out to see the exceptions: 
                if True:#try:
                        if arg4:self.ret=self.method(arg1,arg2,arg3,arg4)
                        elif arg3:self.ret=self.method(arg1,arg2,arg3)
                        elif arg2:self.ret=self.method(arg1,arg2)
                        elif arg1:self.ret=self.method(arg1)
                        else:self.ret=self.method()
                #except Exception,e:self.exception=str(e)+"\n"+str(sys.exc_info()[0])
                self.done=True
        def wait(self,timeout=30):
                #wait till done
                tick=0
                while not self.done:
                        time.sleep(1)
                        tick+=1
                        if tick>=timeout:break
                return self.done
test_instance=None

def function_listentesthandler(addr1,addr2):
        global test_instance
        test_instance.listenreturn=(addr1,addr2)
        
def function_handle_session_handler(data):
        global test_instance
        test_instance.handle_session_data=data

class test(unittestlib.TestCase):
        EOL='\r\n'
        #test cases assume the type checking of arguments is correct
        def test_connect(self):
                #try connecting to a hopefully nonexistant port
                self.assertException(IOError,commlib.connect,'127.0.0.1',6666)
                #test a non-existant host
                self.assertException(IOError,commlib.connect,'this.should.never.exist.edu',80)
                #test with a real socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                hostport=random.randint(4000,60000)
                sock.bind(('127.0.0.1', hostport))
                sock.listen(5)
                sockaccept=async_run(sock.accept)
                try:commlib.connect('127.0.0.1',hostport)
                except:pass
                #wait for connection:
                sockaccept.wait(60)
                #if it's connected, then the accept should be finished as well
                self.assertFalse(commlib.glo_comm is None)
                self.assertTrue(type(sockaccept.ret)==tuple)
                #just to be sure
                print "Accepted Socket:",sockaccept.ret
                #close the socket
                try:commlib.disconnect()
                except:pass
                sock.close()
        
        def listentesthandler(self,addr1,addr2):
                self.listenreturn=(addr1,addr2)
        
        def test_listen(self):
                """NOTICE: the arizonacomm.listen method cannot be stopped, so this will leave threads running and require that
                the test be killed once completed.
                """
                global test_instance
                test_instance=self
                #test if it checks the min/max of the max_pending argument?
                # skip it - just passed through and the user is assumed to be smart enough to pick a valid value to send or use the default
                # also, using negative values does not seem to cause any exceptions, so below zero might be treated as zero
                
                #only test reasonably possible - test if it handles correct arguments as assumed to
                # done twice to test if accepting both types of 'functions'
                hostport=random.randint(4000,60000)
                self.listenreturn=None
                listen1 = async_run(commlib.listen,'127.0.0.1',hostport,function_listentesthandler)
                #connect:
                time.sleep(3) #ensure the listener started 
                sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                sock.connect(('127.0.0.1',hostport))
                time.sleep(3) #to ensure the handler finished
                #assumed to have connected and closed itself
                self.assertFalse(listen1.done) #should still be going
                #check the return value
                self.assertTrue(type(self.listenreturn)==tuple)
                self.assertFalse(commlib.glo_comm is None)
                #second test
                self.listenreturn=None
                sock.close() 
                listen2 = async_run(commlib.listen,'127.0.0.1',hostport+1,self.listentesthandler)
                time.sleep(3) 
                #assume it accepted the method instead of function type
                #connect:
                sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                sock.connect(('127.0.0.1',hostport+1))
                time.sleep(3) #to ensure the handler finished
                #assumed to have connected and closed itself
                self.assertFalse(listen2.done) #should still be going
                #check the return value
                self.assertTrue(type(self.listenreturn)==tuple)
                self.assertFalse(commlib.glo_comm is None)
                sock.close()
        
        def handle_session_handler(self,data):
                self.handle_session_data=data+"1"
        def handle_session_handler2(self,data):
                self.handle_session_data=data+"2"
        def handle_session_handler3(self,data):
                self.handle_session_data=data+'3'
        
        def socket_send(self,sock,txt):
                while len(txt)>0:
                        sent=sock.send(txt)
                        txt=txt[sent:]
        
        def test_handle_session(self):
                #this could be slightly complicated...
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                hostport=random.randint(4000,60000)
                sock.bind(('127.0.0.1', hostport))
                sock.listen(5)
                host= async_run(sock.accept)
                commlib.connect('127.0.0.1',hostport)
                #wait for connection:
                host.wait(60)
                #check the length check of handle session (and assume it passes so it can continue)
                self.assertException(TypeError,commlib.handle_session,{'[Update':function_handle_session_handler},'[[')
                #assume that passing it methods instead of functions won't raise an exception
                handlesession=async_run(commlib.handle_session,{'[Test1':self.handle_session_handler,'[test1':self.handle_session_handler2,'[Test[3]':self.handle_session_handler3},'[')#using a different escape char here for testing
                #test 1
                self.handle_session_data=None
                self.socket_send(host.ret[0],'BigData[Test1'+self.EOL)
                time.sleep(3)
                self.assertEquals(self.handle_session_data,'BigData1')
                self.assertFalse(handlesession.done)
                #try sending the check_connection message
                commlib.check_connection()
                host.ret[0].sendall("####"+self.EOL) 
                host.ret[0].sendall("####"+self.EOL) 
                time.sleep(5)
                #ensure the connection is still live
                self.assertFalse(handlesession.done) 
                self.handle_session_data=None
                commlib.check_connection() 
                host.ret[0].sendall("####"+self.EOL) 
                host.ret[0].sendall("####"+self.EOL) 
                self.socket_send(host.ret[0],'  Big[[Data]\n[Test1'+self.EOL)
                time.sleep(3)
                self.assertFalse(handlesession.done)
                self.assertEquals(self.handle_session_data,'  Big[Data]\n1')
                #test 2
                self.handle_session_data=None
                self.socket_send(host.ret[0],'NiceTest[test1'+self.EOL)
                time.sleep(3)
                self.assertFalse(handlesession.done)
                self.assertEquals(self.handle_session_data,'NiceTest2')
                #test 3 # was a test for commands not starting with escape sequences.
                #self.handle_session_data=None
                #self.socket_send(host.ret[0],'TestData[Test3')
                #time.sleep(3)
                #self.assertFalse(handlesession.done)
                #self.assertTrue(handlesession.exception is None)
                #self.assertEquals(self.handle_session_data,'TestData3')
                #test 3.2 #test for commands containing escape sequences
                self.handle_session_data=None
                self.socket_send(host.ret[0],'TestData[Test[3]'+self.EOL)
                time.sleep(3)
                self.assertFalse(handlesession.done)
                self.assertTrue(handlesession.exception is None)
                self.assertEquals(self.handle_session_data,'TestData3')
                #test 4 #test for disconnecting when receiving a non-existant command.
                self.handle_session_data=None
                self.socket_send(host.ret[0],'TestData[Test89'+self.EOL)
                time.sleep(3)
                self.assertTrue(handlesession.done)
                self.assertTrue(self.handle_session_data is None)
                sock.close()

        def test_send(self):
                #
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                hostport=random.randint(4000,60000)
                sock.bind(('127.0.0.1', hostport))
                sock.listen(5)
                sockaccept=async_run(sock.accept)
                commlib.connect('127.0.0.1',hostport)
                #wait for connection
                sockaccept.wait(60)
                #should be connected now.
                self.assertTrue(sockaccept.done) 
                receiver=async_run(sockaccept.ret[0].recv,4096)
                commlib.send('[you','spin me','[')
                #wait for completion:
                receiver.wait(60)
                self.assertEqual(receiver.ret,'spin me[[you'+self.EOL)
                
                receiver=async_run(sockaccept.ret[0].recv,4096)
                commlib.send('[right','round [baby]','[')
                #wait for completion:
                receiver.wait(60)
                self.assertEqual(receiver.ret,'round [[baby][[right'+self.EOL)
                
                receiver=async_run(sockaccept.ret[0].recv,4096)
                commlib.send('[right',' round [like] [a] record[baby]\n','[')
                #wait for completion:
                receiver.wait(60)
                self.assertEqual(receiver.ret,' round [[like] [[a] record[[baby]\n[[right'+self.EOL)
                
                receiver=async_run(sockaccept.ret[0].recv,4096)
                commlib.send('[right [round]','round round','[')
                #wait for completion:
                receiver.wait(60)
                self.assertEqual(receiver.ret,'round round[[right [round]'+self.EOL)
                
                receiver=async_run(sockaccept.ret[0].recv,4096)
                commlib.send('[you [spin]\n','me [right] round [baby]','[')
                #wait for completion:
                receiver.wait(60)
                self.assertEqual(receiver.ret,'me [[right] round [[baby][[you [spin]\n'+self.EOL)
                
        def test_disconnect(self):
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                hostport=random.randint(4000,60000) #assumedly with a large range, this won't conflict with anything that might still be listening
                sock.bind(('127.0.0.1', hostport))
                sock.listen(5)
                sockaccept=async_run(sock.accept)
                commlib.connect('127.0.0.1',hostport)
                #wait for connection:
                sockaccept.wait(60)
                self.assertFalse(commlib.glo_comm is None)
                commlib.send("nothing","nothing","n")
                commlib.disconnect()
                self.assertTrue(commlib.glo_stop)

        ## check_connection test ##
        
        def test_check_connection(self):
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                hostport=random.randint(4000,60000) #assumedly with a large range, this won't conflict with anything that might still be listening
                sock.bind(('127.0.0.1', hostport))
                sock.listen(5)
                #test 1:
                sockaccept=async_run(sock.accept)
                commlib.connect('127.0.0.1',hostport)
                #wait for connection:
                sockaccept.wait(60)
                self.assertTrue(commlib.check_connection())
                #test 1.2:
                sockaccept.ret[0].close()
                self.assertFalse(commlib.check_connection())
                #test 1.3:
                commlib.disconnect()
                self.assertFalse(commlib.check_connection())
                #test 2:
                sockaccept=async_run(sock.accept)
                sock2=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                sock2.connect(('127.0.0.1',hostport))
                #wait for connection:
                sockaccept.wait(60)
                sock2.setblocking(0)
                self.assertTrue(commlib.check_connection(sock2,True))
                #test 2.1:
                sockaccept.ret[0].close()
                self.assertFalse(commlib.check_connection(sock2,True))
                #test 2.2:
                sock2.close()
                self.assertFalse(commlib.check_connection(sock2,True))
                #tes 2.3:
                self.assertFalse(commlib.check_connection(None,True))
                
        ## single_conn tests ##
        
        def test_single_conn_connect(self):
                #create a single_conn
                sconn=commlib.single_conn('127.0.0.1',6666,{'[Update':self.handle_session_handler},None,'[',False,True)
                #try connecting to a hopefully nonexistant port
                self.assertFalse(sconn.connect('127.0.0.1',6666))
                #test a non-existant host
                self.assertFalse(sconn.connect('this.should.never.exist.edu',80))
                #test with a real socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                hostport=random.randint(4000,60000)
                sock.bind(('127.0.0.1', hostport))
                sock.listen(5)
                sockaccept=async_run(sock.accept)
                self.assertTrue(sconn.connect('127.0.0.1',hostport))
                #wait for connection:
                sockaccept.wait(60)
                #if it's connected, then the accept should be finished as well
                self.assertTrue(sconn.connected)
                self.assertTrue(type(sockaccept.ret)==tuple)
                #just to be sure
                print "Accepted Socket:",sockaccept.ret
                #close the socket
                sconn.stop()
                sock.close()
        
        def test_single_conn_disconnect(self):
                #create a single_conn
                sconn=commlib.single_conn('127.0.0.1',6666,{'[Update':self.handle_session_handler},None,'[',False,True)

                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                hostport=random.randint(4000,60000) #assumedly with a large range, this won't conflict with anything that might still be listening
                sock.bind(('127.0.0.1', hostport))
                sock.listen(5)
                sockaccept=async_run(sock.accept)
                self.assertTrue(sconn.connect('127.0.0.1',hostport))
                #wait for connection:
                sockaccept.wait(60)
                sconn.send('nothing','nothing','n')
                sconn.disconnect()
                self.assertFalse(sconn.connected)
                #would test to ensure that sconn.sock is None, but that could be assuming too much about the inner workings
                sock.close()

        def test_single_conn_send(self):
                #create a single_conn
                sconn=commlib.single_conn('127.0.0.1',6666,{'[Update':self.handle_session_handler},None,'[',False,True)

                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                hostport=random.randint(4000,60000)
                sock.bind(('127.0.0.1', hostport))
                sock.listen(5)
                sockaccept=async_run(sock.accept)
                self.assertTrue(sconn.connect('127.0.0.1',hostport))
                #wait for connection:
                sockaccept.wait(60)
                #should be connected now.
                receiver=async_run(sockaccept.ret[0].recv,4096)
                sconn.send('[you','spin me','[')
                #wait for completion:
                receiver.wait()
                self.assertEqual(receiver.ret,'spin me[you'+self.EOL)
                
                receiver=async_run(sockaccept.ret[0].recv,4096)
                sconn.send('[right','round [baby]','[')
                #wait for completion:
                receiver.wait()
                self.assertEqual(receiver.ret,'round [[baby][right'+self.EOL)
                
                receiver=async_run(sockaccept.ret[0].recv,4096)
                sconn.send('[right',' round [like] [a] record[baby]\n','[')
                #wait for completion:
                receiver.wait()
                self.assertEqual(receiver.ret,' round [[like] [[a] record[[baby]\n[right'+self.EOL)
                
                receiver=async_run(sockaccept.ret[0].recv,4096)
                sconn.send('[right [round]','round round','[')
                #wait for completion:
                receiver.wait()
                self.assertEqual(receiver.ret,'round round[right [[round]'+self.EOL)
                
                receiver=async_run(sockaccept.ret[0].recv,4096)
                sconn.send('[you [spin]\n','me [right] round [baby]','[')
                #wait for completion:
                receiver.wait()
                self.assertEqual(receiver.ret,'me [[right] round [[baby][you [[spin]\n'+self.EOL)
                sconn.stop()
                sock.close()
                
        def test_single_conn_recv(self):
                #create a single_conn
                sconn=commlib.single_conn('127.0.0.1',6666,{'[Update':self.handle_session_handler},None,'[',False,True)

                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                hostport=random.randint(4000,60000)
                sock.bind(('127.0.0.1', hostport))
                sock.listen(5)
                sockaccept=async_run(sock.accept)
                self.assertTrue(sconn.connect('127.0.0.1',hostport))
                #give it a minute to connect:
                sockaccept.wait(60)
                #should be connected now. - send a couple messages.
                receiver=async_run(sconn.recv,4096)
                testtxt='THIS IS A TEST.  If This were a real emergency...\n'
                sockaccept.ret[0].send(testtxt)
                #wait for completion:
                receiver.wait()
                self.assertEqual(receiver.ret,testtxt)
                
                receiver=async_run(sconn.recv,4096)
                testtxt='If you are reading this, thank a teacher... or the internet...'
                sockaccept.ret[0].send(testtxt)
                #wait for completion:
                receiver.wait()
                self.assertEqual(receiver.ret,testtxt)
                sconn.stop()
                sock.close()

        def test_single_conn_default_handler(self):
                #create a single_conn
                sconn=commlib.single_conn('127.0.0.1',6666,{'[Update':self.handle_session_handler},None,'[',False,True)

                #this could be slightly complicated...
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                hostport=random.randint(4000,60000)
                sock.bind(('127.0.0.1', hostport))
                sock.listen(5)
                host= async_run(sock.accept)
                self.assertTrue(sconn.connect('127.0.0.1',hostport))
                #wait for connection
                host.wait(60)
                #check the length check of handle session (and assume it passes so it can continue)
                self.assertException(TypeError,sconn.default_handler,{'[Update':function_handle_session_handler},None,'[[')
                #assume that passing it methods instead of functions won't raise an exception
                handlesession=async_run(sconn.default_handler,{'[Test1':self.handle_session_handler,'[test1':self.handle_session_handler2,'[Test[3]':self.handle_session_handler3},None,'[')#using a different escape char here for testing
                #test 1
                self.handle_session_data=None
                self.socket_send(host.ret[0],'BigData[Test1'+self.EOL)
                time.sleep(3)
                self.assertEquals(self.handle_session_data,'BigData1')
                self.assertFalse(handlesession.done)
                #test 1.2
                self.handle_session_data=None
                self.socket_send(host.ret[0],'  Big[[Data]\n[Test1'+self.EOL)
                time.sleep(3)
                self.assertFalse(handlesession.done)
                self.assertEquals(self.handle_session_data,'  Big[Data]\n1')
                #test 2
                self.handle_session_data=None
                self.socket_send(host.ret[0],'NiceTest[test1'+self.EOL)
                time.sleep(3)
                self.assertFalse(handlesession.done)
                self.assertEquals(self.handle_session_data,'NiceTest2')
                #test 3 # was a test for commands not starting with escape sequences.
                #self.handle_session_data=None
                #self.socket_send(host.ret[0],'TestData[Test3')
                #time.sleep(3)
                #self.assertFalse(handlesession.done)
                #self.assertTrue(handlesession.exception is None)
                #self.assertEquals(self.handle_session_data,'TestData3')
                #test 3.2 #test for commands containing escape sequences
                self.handle_session_data=None
                self.socket_send(host.ret[0],'TestData[Test[[3]'+self.EOL)
                time.sleep(3)
                self.assertFalse(handlesession.done)
                self.assertTrue(handlesession.exception is None)
                self.assertEquals(self.handle_session_data,'TestData3')
                #test 4 #test for disconnecting when receiving a non-existant command.
                self.handle_session_data=None
                self.socket_send(host.ret[0],'TestData[Test89'+self.EOL)
                time.sleep(3)
                self.assertTrue(handlesession.done)
                self.assertTrue(self.handle_session_data is None)
                sock.close()
                sconn.stop()

        def test_single_conn_run(self):
                hostport=random.randint(4000,60000)
                #create a single_conn
                sconn=commlib.single_conn('127.0.0.1',hostport,{'[Update':self.handle_session_handler},None,'[',False,True)
                sconn.retrysleep=10 #10 seconds between tries

                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind(('127.0.0.1', hostport))
                sock.listen(5)
                sockaccept=async_run(sock.accept)
                sconn.start()
                #wait for connection:
                sockaccept.wait(60)
                self.assertTrue(sconn.connected)
                sockaccept.ret[0].close()
                time.sleep(5)
                #wont work since it will automatically attempt to reconnect 
                #self.assertFalse(sconn.connected)
                sockaccept=async_run(sock.accept)
                #wait for connection:
                sockaccept.wait(60)
                #should be reconnected
                self.assertTrue(sconn.connected)
                self.assertTrue(sockaccept.done and not sockaccept.ret is None)
                sock.close()
                sconn.stop()

        ## listener tests ##
        def test_listener_run(self):
                hostport=random.randint(4000,60000)
                #create a listener
                lst=commlib.listener(hostport,None,None,5,False)

                lstrun=async_run(lst.run)
                self.assertFalse(lstrun.done)
                time.sleep(3)#ensure the listener started 
                sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                sock.connect(('127.0.0.1',hostport))
                time.sleep(3)
                self.assertTrue(len(lst.connlist)>0)
                self.assertEqual(len(lst.connlist),1)

                sock.close()
                lst.default_list_check()
                self.assertEqual(len(lst.connlist),0)
                #stop test
                lst.stop()
                sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                sock.connect(('127.0.0.1',hostport))
                self.assertTrue(lst.done)
                time.sleep(3) 
                self.assertTrue(lstrun.done)             
                
if __name__=='__main__':
        unittestlib.main(test)
