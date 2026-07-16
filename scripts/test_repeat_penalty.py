import inspect
from llama_cpp import Llama

# Look at the signature of the primary text-completion function
sig = inspect.signature(Llama.__call__)

# Print out the default values assigned to the repeat parameters
print(f"Default repeat_penalty: {sig.parameters['repeat_penalty'].default}")
print(f"Default presence_penalty: {sig.parameters['presence_penalty'].default}")
print(f"Default frequency_penalty: {sig.parameters['frequency_penalty'].default}")
