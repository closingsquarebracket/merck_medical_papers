import tensorflow as tf
from attention_layer import AttentionWithContext

# TODO: Define 3 Models: Metadata only, Abstract only, combination of both. Basis for the input should be an xml file.
# TODO: Ensure validation of the xml file before processing. Keywords, abstract, names should be correctly captured.

inputs_abstract = tf.keras.Input(shape = (None, embedding_size))
