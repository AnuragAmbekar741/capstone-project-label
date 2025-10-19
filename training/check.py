
import sys, transformers, inspect
import transformers.generation.utils as g
print("SCRIPT OK — using Transformers, not custom_generate.")
print("TRANSFORMERS VERSION:", transformers.__version__)
print("GENERATION UTILS  :", g.__file__)
print("WORKING DIR       :", __import__("os").getcwd())
print("FIRST PATH ENTRIES:", sys.path[:5])
