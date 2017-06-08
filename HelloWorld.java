import java.io.IOException;


public class HelloWorld {
	

	

	public static void main(String[] args) throws IOException {
		// TODO Auto-generated method stub
		System.out.println("Hello World!");
		
		Parser p = new Parser();
		
		
		p.ParseAndGenerateMatrix("C:\\Users\\Ben\\workspace\\HelloWorld\\src\\rule.txt");
	
		
		p.TestStrings("C:\\Users\\Ben\\workspace\\HelloWorld\\src\\test.txt");
				
		
		
		
	}


}

