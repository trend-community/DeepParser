import logging
import Tokenization, FeatureOntology


if __name__ == "__main__":
    logging.basicConfig( level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
    target = "This is a 'bad_sentence', not a word. Don't classify it as a character. airline"
    nodes = Tokenization.Tokenize(target)
    for node in nodes:
        node.features = FeatureOntology.SearchFeatures(node.word)

    for node in nodes:
        output = "Node [" + node.word + "]:"
        for featureID in node.features:
            output += FeatureOntology.GetFeatureName(featureID) + ";"
        print output

