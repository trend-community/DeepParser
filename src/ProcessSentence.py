import logging
import Tokenization, FeatureOntology


if __name__ == "__main__":
    logging.basicConfig( level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
    target = "This ised a 'bad_sentence', not a word. Don't classify it as  characters. airline"
    nodes = Tokenization.Tokenize(target)
    for node in nodes:
        node.features = FeatureOntology.SearchFeatures(node.word)

    #default lexY.txt is already loaded. additional lexicons can be load here:
    #FeatureOntology.LoadLexicon("../../fsa/X/lexX.txt")
    for node in nodes:
        output = "Node [" + node.word + "]:"
        for featureID in node.features:
            output += FeatureOntology.GetFeatureName(featureID) + ";"
        print output

