"""
This script applies the data preprocessing steps for the example file that is generated for use with the X3ML mapping tool.
"""

from lib.Preprocessors import Preprocessors

def applyPreprocessing(*, file, module):
    preprocessor = Preprocessors.getPreprocessor(module)
    print("Preprocessing file:", file, "with module:", module)
    with open(file, 'r') as f:
        contents = f.read()
        contents = preprocessor.preprocess(contents)
    with open(file, 'w') as f:
        f.write(contents)

if __name__ == "__main__":
    import argparse
    from os.path import join
    from lib.Preprocessors import Preprocessors

    parser = argparse.ArgumentParser()

    parser = argparse.ArgumentParser(description='Preprocess data for example file', allow_abbrev=False)
    parser.add_argument('--file', required=True, help='Name of the file to preprocess')
    parser.add_argument('--module', required=True, help='Name of the module to process the data form')
    args, _ = parser.parse_known_args()

    applyPreprocessing(file=args.file, module=args.module)