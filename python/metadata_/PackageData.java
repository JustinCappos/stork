package metadata_;

import java.io.File;
import java.io.IOException;

public class PackageData {
	private static  MetaData reader;
	
		
	/**
	 * @param filename [provides|requires|files|package]
	 * @throws IOException 
	 */
	public static void main(String[] args) throws IOException {
		boolean works = false;
		 File dir = new File("metadata_/stubs_");
		 File[] stubs = dir.listFiles();
		 for(int x=0; x< stubs.length; x++){
			 //System.out.println(stubs[x].getCanonicalPath());
			 if(stubs[x].getName().endsWith("class")){
				 try{
					 Class c = Class.forName("metadata_.stubs_."+stubs[x].getName().replace(".class", ""));
					 reader = (MetaData) c.newInstance();
					 if(reader.works(args[0])){
					 	 reader.setFile(args[0]);
						 works = true;
						 if(args[1].contains("provides")){
							 System.out.println(reader.getProvides());
						 }else if(args[1].contains("requires")){
							 System.out.println(reader.getRequires());
						 }else if(args[1].contains("files")){
							 System.out.println(reader.getFiles());
						 }else if(args[1].contains("package")){
							 System.out.println(reader.getPackageData());
						 }
						 break;
					 }
				 }catch(ClassNotFoundException e){
					 e.printStackTrace();
					 System.err.println(e.getLocalizedMessage());
				 } catch (InstantiationException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
					 System.err.println(e.getLocalizedMessage());

				} catch (IllegalAccessException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
					 System.err.println(e.getLocalizedMessage());

				}
			 }
		 }
		 if(!works){
                        if(args.length == 0)
                            System.out.println("No file given");
                        else
			 System.out.println("No parser for *"+args[0]+" file types"+
					   "\nPackages will not be added to repository listing.");
		 }
		

	}

}
