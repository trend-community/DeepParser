
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.MalformedURLException;
import java.net.URL;
import java.net.URLEncoder;


import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;
import org.json.simple.parser.ParseException;

public class App_TestClient {
	// http://localhost:8080/RESTfulExample/json/product/get
	public static void main(String[] args) throws ParseException {

		try {
			String urljsonlink = "http://localhost:5001/LexicalAnalyze?Key=Lsdif238fj&Type=json&Sentence=";

			String query2 = "昨天我买了香奈儿眉笔";

			URL urljson = new URL(urljsonlink + "\"" + URLEncoder.encode(query2, "UTF-8") + "\"");
			BufferedReader in2 = new BufferedReader(new InputStreamReader(urljson.openStream()));

			String inputLine2 = in2.readLine();
			System.out.println(inputLine2);
			in2.close();

			JSONParser parser = new JSONParser();
			Object obj;
			try {
				obj = parser.parse(inputLine2);
				JSONObject root = (JSONObject) obj;
				DisplayParsetree(root, 0);
			} catch (ParseException e) {
				e.printStackTrace();
			}

		} catch (MalformedURLException e) {
			e.printStackTrace();
		} catch (IOException e) {
			e.printStackTrace();
		}
	}

	public static void DisplayParsetree(JSONObject obj, int depth) {
		String Text = (String) obj.get("text");
		for (int i = 0; i < depth; i++)
			System.out.print("    ");

		System.out.print("Text=" + Text);
		JSONArray Features = (JSONArray) obj.get("features");
		if ((Features != null) && (Features.size() > 0)) {
			System.out.print("[");
			for (Object f : Features)
				System.out.print((String) f + " ");
			System.out.print("]");
		}
		String UpperRelationship = (String) obj.get("UpperRelationship");
		if (UpperRelationship != null)
			System.out.print("(" + UpperRelationship + ")");

		System.out.print("\n");
		JSONArray sons = (JSONArray) obj.get("sons");
		if (sons != null) {
			for (Object o : sons) {
				DisplayParsetree((JSONObject) o, depth + 1);
			}
		}
	}
}

// Usage: step 1, download json-simple from https://code.google.com/archive/p/json-simple/downloads
// step 2, compile: javac -cp ~/Downloads/json-simple-1.1.1.jar: App_TestClient.java
// step 3, running: java -cp ~/Downloads/json-simple-1.1.1.jar: App_TestClient