
public class RuleMatrix {
	int ID;
	String ruleName;
	int[][] matrix;
	int successState = 0;

	int MaxStates = 10;
	int MaxVocabularies = 10;
	
	public String toString(){
		return "[" + String.valueOf(ID) + "] [" + ruleName + "]";
	}
	
	public RuleMatrix(){
		matrix = new int[MaxStates][MaxVocabularies];
	}
}
