import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.file.Files;

import java.nio.file.Paths;
import java.util.HashSet;
import java.util.Set;


public class Parser {

	Set<RuleMatrix> rules;
	static int index = 0;
	static String[] Vocabulary = {"[word]", "[RB]", "[Adv]"};

	
	public Parser(){
		rules = new HashSet<RuleMatrix>();
	}

	public static void main(String[] args) throws IOException {
		Parser p = new Parser();
		
		
		p.ParseAndGenerateMatrix("data/rule.txt");
	
		
		p.TestStrings("data/test.txt");
					
	}
	

	public void TestStrings(String testFileLocation) throws IOException {
		// TODO Auto-generated method stub
		try (BufferedReader br = new BufferedReader(new FileReader(testFileLocation))) {
		    String line;
		    while ((line = br.readLine()) != null) {
		       // process the line.
		    	line = line.trim();
		    	String normalizedLine = Normalize(line);
		    	for(RuleMatrix rm : rules){
		    		if (RuleMatch(rm, normalizedLine)){
		    			System.out.println("Found rule: " + rm.toString() + " for line " + System.getProperty("line.separator") + line);
		    		}
		    	}
		    	
		    }
		}
		
	}

	
	private boolean RuleMatch(RuleMatrix rm, String normalizedLine) {
		int stateIndex = 0;
		for (int i = 0; i < normalizedLine.length(); i++){
			for(int j=0; j<Vocabulary.length; j++){
				String v = Vocabulary[j];
				if (i+v.length() <= normalizedLine.length()){
					if (normalizedLine.substring(i, i+v.length()).equals(v)){
						
						//v is matched in the rule. the index is j. so the state should be .
						stateIndex = rm.matrix[stateIndex][j];
						if (stateIndex == 0){
							return false;
						}
						else{
							i += v.length();
							break;	// should finish the loop of j (Vocabulary) and go to the next i;
						}
					}
				}
			}
		}
		
		if (stateIndex == rm.successState)
			return true;
		else
			return false;
	}


	private String Normalize(String line) {
		String [] words = line.split(" ");
		for (int index =0; index < words.length; index++){
			words[index] = "[word]";		//first version, not checking for RB or Adv...
		}
		String normalized = String.join(" ", words);
		
		return normalized;
	}


	private String readFile(String path) 			  throws IOException 	{
		Charset encoding = Charset.defaultCharset();
		byte[] encoded = Files.readAllBytes(Paths.get(path));
		return new String(encoded, encoding);
		}
	
	
	public void ParseAndGenerateMatrix(String ruleFileLocation) throws IOException {
		String ruleString = readFile(ruleFileLocation);
		String [] rules = ruleString.split(";");
		for (String rule : rules){
			rule = rule.trim();
			CompileRule(rule);
		}
		
		
	}


	private void CompileRule(String ruleString) {
		
		RuleMatrix rule = new RuleMatrix();
		rule.ID = index++;
		String[] parts = ruleString.split("=");
		if (parts.length != 2)
			return;					//the rule is not correctly separated using "=".
		rule.ruleName = parts[0]; 
		String ruleContent = parts[1]; 
		
		
		int stateIndex = 0;
		for (int i = 0; i < ruleContent.length(); i++){
			for(int j=0; j<Vocabulary.length; j++){
				String v = Vocabulary[j];
				if (i+v.length() <= ruleContent.length()){
					if (ruleContent.substring(i, i+v.length()).equals(v)){
						
						//v is matched in the rule. the index is j. so the state should be +1.
						rule.matrix[stateIndex][j] = stateIndex+1;
						stateIndex++;
						i+=v.length()-1;
						break;		//jump out of loop j. no longer look for vocabulary for this part.
					}
				}
			}
		}
		
		rule.successState = stateIndex;	//The last state is success state.
		
		
		rules.add(rule);

	}
}
