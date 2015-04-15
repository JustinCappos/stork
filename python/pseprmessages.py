#written by Jason Hardies while working with the Stork project at the U of Arizona - FA05

#Message definitions:

#The initial connection message:
connect1="""<?xml version="1.0" encoding="UTF-8" ?>
<stream:stream to="%s"
xmlns="jabber:client"
xmlns:stream="http://etherx.jabber.org/streams">"""

#The initial logon message -- sent right after connect1
logon1="""<iq xmlns="jabber:client" type='get' id='%s'>
<query xmlns="jabber:iq:auth">
  <username>%s</username>
</query>
</iq>
"""

#Second logon message -- sent after logon1 after receiving another reply
#note: password is plaintext
logon2="""<iq xmlns="jabber:client" type='set' id='%s'>
<query xmlns="jabber:iq:auth">
  <username>%s</username>
  <password>%s</password>
  <resource>Home</resource>
</query>
</iq>
"""

#The channel subscription message:
subscribe1="""<message to='psepr_registry@jabber.services.planet-lab.org' id='%s'>
  <x seconds='60' xmlns='jabber:x:expire'/>
  <event xmlns='http://psepr.org/xs/event'>
    <to>
      <channel>%s</channel>
      <service>psepr_router</service>
      <instance></instance>
    </to>
    <from>
      <service>%s</service>
      <instance>%s/list/nodes/</instance>
    </from>
    <payload xmlns='http://psepr.org/xs/payload/lease'>
      <duration>%d</duration>
      <identifier>%s</identifier>
      <op>register</op>
    </payload>
  </event>
</message>
""" #(id,channel,username,username(or random name -- hostname of node?),duration (%d),leaseid)

#Basic message format:
message1="""<message to='psepr_registry@jabber.services.planet-lab.org' id='%s'>
    <x seconds="60" xmlns="jabber:x:expire"/>
    <event xmlns="http://psepr.org/xs/event">
      <to>
          <channel>%s</channel>
      </to>
      <from>
          <service>%s</service>
          <instance>%s/list/nodes/</instance>
      </from>
      <payload xmlns="http://psepr.org/xs/payload/attribute">
          <field>%s</field>
          <value>%s</value>
          <expire>%d</expire>
      </payload>
  </event>
</message>
"""#(id,channel,username,username(or id--hostname of node?),fieldname,value,expiration)

#Basic message format with addition of a specific service to send to
message2="""<message to='psepr_registry@jabber.services.planet-lab.org' id='%s'>
    <x seconds="60" xmlns="jabber:x:expire"/>
    <event xmlns="http://psepr.org/xs/event">
      <to>
          <channel>%s</channel>
          <service>%s</service>
      </to>
      <from>
          <service>%s</service>
          <instance>%s/list/nodes/</instance>
      </from>
      <payload xmlns="http://psepr.org/xs/payload/attribute">
          <field>%s</field>
          <value>%s</value>
          <expire>%d</expire>
      </payload>
  </event>
</message>
"""#(id,channel,service,username,username(or id--hostname of node?),fieldname,value,expiration)

#Basic message, directed at a service and instance
message3="""<message to='psepr_registry@jabber.services.planet-lab.org' id='%s'>
    <x seconds="60" xmlns="jabber:x:expire"/>
    <event xmlns="http://psepr.org/xs/event">
      <to>
          <channel>%s</channel>
          <service>%s</service>
          <instance>%s</instance>
      </to>
      <from>
          <service>%s</service>
          <instance>%s/list/nodes/</instance>
      </from>
      <payload xmlns="http://psepr.org/xs/payload/attribute">
          <field>%s</field>
          <value>%s</value>
          <expire>%d</expire>
      </payload>
  </event>
</message>
"""#(id,tochannel,toservice,toinstance,username,username(or id--hostname of node?),fieldname,value,expiration)

#Message with authentification information included.
message4= """<inputEvent>
  <authentication>
    <passwordAuth>
      <service>%s</service>
      <password>%s</password>
    </passwordAuth>
  </authentication>
  <oneEvent>
    <event xmlns="http://psepr.org/xs/event">
      <to>
          <channel>%s</channel>
          <service>%s</service>
      </to>
      <from>
          <service>%s</service>
          <instance>%s/list/nodes/</instance>
      </from>
      <payload xmlns="http://psepr.org/xs/payload/attribute">
          <field>%s</field>
          <value>%s</value>
      </payload>
  </event>
  </oneEvent>
</inputEvent>
"""
