import java.util.TreeSet;
import java.util.Set;

public class OntologyRule implements Comparable<OntologyRule> {
	static int MAXRULELENGTH=1000;
	static int MAXFEATURENUM=5000;
	static String featureList[] = new String[MAXFEATURENUM];
	
	//alias: Each alias can only have one root. 
	private class Alias implements Comparable<Alias>{
		String aliasName;
		int featureID;	//index in the featureList;
		void SetAlias(String alias, int featureID){
			this.aliasName = alias.trim();
			this.featureID = featureID;
		}
		
		public int compareTo(Alias other){
			return this.aliasName.compareTo(other.aliasName);
		}
	}
	static Set<Alias> aliasList = new TreeSet<Alias>();
	
	String openWord;
	int parents[];
	String comment;
	
	
	public OntologyRule(){
		this.parents = new int[MAXRULELENGTH];
		if (featureList[0] == null){
			featureList[0] = "VOID_AS_START";	//it's illegal to use "0" as ancester.
			featureList[1] = ";";				// as a separater if needed.
		}
	}
	
	
	public int compareTo(OntologyRule other){
		return this.openWord.compareTo(other.openWord);
	}
	
	
	public void setRule(String line){
		// syntax: the first word is openword; ";" separated parents; "," separated ancesters.
		String code = removeComment(line);
		code = processAlias(code);
		int firstcomma = code.indexOf(',');
		if (firstcomma<=0){
			firstcomma = code.indexOf(';');		//line 146:PRP=pro; pn // PRP can retire in time . The syntax is illegal, but let's process it.
			if (firstcomma <= 0)
				return;
		}
		
		openWord = code.substring(0,  firstcomma).trim();
		openWord = featureList[findNode(openWord)];		//Might be modify if this openWord was an alias.
		String rule = code.substring(firstcomma+1).trim();
		String parents[] = rule.split(";");				//Now ";" and "," are treated equally. But we might change that in the future. So process them separately.
		for (int i=0; i<parents.length; i++){
			String ancesters[] = parents[i].split(",");
			for (int j=0; j<ancesters.length; j++){
				markAncester(ancesters[j]);	
			}
		}
	}
	
	
	private int findNode(String featureName) {
		featureName = featureName.trim();
		// If this featureName is an alias, use the real id
		for (Alias a : aliasList){
			if (a.aliasName.equals(featureName)){
				return a.featureID;
			}
		}
		
		int index;
		for(index=0; index<featureList.length; index++){
			if (featureList[index] == null)
				break;	//to the end of featureList;
			if (featureList[index].equals(featureName))
				break;	//found it!
		}
		if (index >= featureList.length){
			//throw(Exception("Out of bound: featureList is not big enough"));
			System.out.println("Out of bound: featureList is not big enough");
			return 0;
		}
		if (featureList[index] == null){
			featureList[index] = featureName;
		}
		
		return index;
	}
	
	
	private void markAncester(String featureName) {
		int index = findNode(featureName);
		for(int j=0; j<parents.length; j++){
			if (parents[j] == 0){			//Find the last item. 
				parents[j] = index;
				break;
			}
		}
	}

	
	private String removeComment(String line) {
		String[] output = line.split("//");
		if (output.length > 1){
			comment = output[1];
		}
		return output[0].trim();
	}
	
	
	private String processAlias(String line) {
		String[] output = line.split("=");
		if (output.length == 1){
			return line;
		}
		
		//The last entity have the real feature name and code;
		String code = output[output.length-1].trim();
		String[] features = code.split(",|;");
		int featureID = findNode(features[0]);
		
		//All items before the last are alias.
		for (int i=0; i<output.length-1; i++){
			Alias a = new Alias();
			a.SetAlias(output[i].trim(), featureID);
			aliasList.add(a);
		}
		
		return code;
	}

	
	public String toString_Alias(){
		String result = "[ALIAS]\n";
		for (Alias a : aliasList){
			result += a.aliasName + "\t";
			result += featureList[a.featureID] + "\n";
		}
		result += "\n[END OF ALIAS]\n";
		return result;
	}
	
	public String toString(){
		String result = "[" + openWord + "]:";
		for (int i=0; i<MAXRULELENGTH; i++){
			if (parents[i] == 0)
				break;
			result += featureList[parents[i]] + ";";		//In the next step, output the represented features.
		}
		
		if (comment != null)
			result += "\t//" + comment;
		return result;
	}

	public static void main(String[] args)  {
		// TODO Auto-generated method stub
		OntologyRule r = new OntologyRule();
		r.setRule("B,Buyu,Kid // Buyu");
		System.out.println(r);
		r = new OntologyRule();
		r.setRule("recipC=recipientC,C,Comp,Arg,Kid; recipient");
		System.out.println(r);
		r = new OntologyRule();
		r.setRule("// purposeC,C,Comp,Arg,Kid // use purposeR instead");
		
		System.out.println(r);
	}

}
