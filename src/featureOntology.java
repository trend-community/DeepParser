import java.io.BufferedReader;

import java.io.FileReader;
import java.io.IOException;

import java.util.TreeSet;
import java.util.Set;

public class featureOntology {

	public static void main(String[] args) throws IOException {
		System.out.println("Hello World!");
		
		featureOntology f = new featureOntology();
		
		f.loadRules("src/featureOntology.txt");
		System.out.println("Features for ObjS:" + f.searchFeature("ObjS"));
		
		System.out.println(f);
				
	}
	

	Set<OntologyRule> rules;

	
	public featureOntology(){
		rules = new TreeSet<OntologyRule>();
	}

	
	public OntologyRule searchFeature(String node) {
		for(OntologyRule rm : rules){
			if (rm.openWord.equals(node))
				return rm;
		}
		return null;
	}
	
	
	public String toString(){
		String result = "";
		for(OntologyRule rm : rules){
			result += rm + "\n";
		}

		OntologyRule rm = rules.iterator().next();
		result += rm.toString_Alias();
		return result;
	}

	
	private void loadRules(String Location) {
		try (BufferedReader br = new BufferedReader(new FileReader(Location))) {
		    String line;
		    while ((line = br.readLine()) != null) {
		    	OntologyRule r = new OntologyRule();
		    	r.setRule(line);
		    	if (r.openWord != null)
		    		rules.add(r);
		    }
		} catch (IOException e) {
			e.printStackTrace();
		}
	}

}
