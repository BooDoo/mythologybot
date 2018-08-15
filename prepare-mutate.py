def prepare(**kwargs):
	model=kwargs['model']
	trees=kwargs['trees']
	outprefix=kwargs['outprefix']

	from simpleneighbors import SimpleNeighbors;
	import spacy;
	print("Loading spacy model: %s" % model);
	nlp = spacy.load(model);
	sim = SimpleNeighbors(300);
	print("feeding vectors into SimpleNeighbors...")
	sim.feed((w.orth_, w.vector) for w in nlp.vocab if w.has_vector)
	print("Preparing binary forest of %i trees" % trees)
	sim.build(trees)
	print("Writing to %s.annoy and %s-data.pkl..." % (outprefix, outprefix))
	sim.save(outprefix)
	print("~~~ That's it — we're done! ~~~")
	return

if __name__ == '__main__':
	import argparse
	example_text = '''examples:

 	python prepare-mutate.py -m en_vectors_web_lg -o vocab_forest -t 30 (defaults)
 	python prepare-mutate.py -m en_core_web_md -o core_web_md_forest
 	python prepare-mutate.py -t 10 -o quick_forest'''

	parser = argparse.ArgumentParser(prog="prepare-mutate",
									 description="Prepare mutation script with Annoy mmap",
									 epilog=example_text,
									 formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument("-m", "--model", type=str, default="en_vectors_web_lg",
			help="which spacy model to use (should have vector data)")
	parser.add_argument("-o", "--outprefix", type=str, default="vocab_forest",
			help="save Annoy index and data PKL with filenames prfefixed this way")
	parser.add_argument("-t", "--trees", type=int, default=30,
			help="how many trees in our binary forest. More trees takes longer but yields accuracy.")
	args = parser.parse_args()

	prepare(**vars(args))
