#!/usr/bin/env python3

import os, sys, random, json, re
import datetime
import wordfilter
import spacy
from simpleneighbors import SimpleNeighbors
from random import choice, sample

global nlp, vocab_forest, all_motifs
nlp = None; vocab_forest = SimpleNeighbors(300); all_motifs = None

def populate_motifs(infile="motifs.txt"):
    global all_motifs
    with open(infile) as f:
        all_motifs = list(l.strip() for l in f.readlines())
    return all_motifs

def init_nlp(**kwargs):
    global nlp, vocab_forest
    nlp = nlp or spacy.load(kwargs.get('model', 'en_vectors_web_lg'))

    # stop words from spacy.en:
    stop_words = ['other', 'she', 'alone', 'hers', 'enough', 'becoming', 'amount', 'himself', 'such', 'sometime', 'noone', 'though', 'thereupon', 'wherever', 'will', 'now', 'therefore', 'forty', 'name', 'whom', 'often', 'unless', 'this', 'whether', 'nothing', 'well', 'along', 'from', 'on', 'should', 'hundred', 'much', 'seems', 'wherein', 'beyond', 'used', 'you', 'except', 'so', 'top', 'even', 'without', 'give', 'and', 'whoever', 'about', 'nor', 'which', 'together', 'an', 'everyone', 'below', 'itself', 'doing', 'mostly', 'many', 'else', 'already', 'elsewhere', 'whereupon', 'were', 'using', 'until', 'mine', 'made', 'nobody', 'some', 'down', 'toward', 'with', 'out', 'has', 'although', 'their', 'sixty', 'somehow', 'full', 'next', 'between', 'by', 'yourselves', 'throughout', 'few', 'own', 'hereafter', 'up', 'done', 'indeed', 'anywhere', 'then', 'latter', 'our', 'same', 'over', 're', 'not', 'regarding', 'nowhere', 'really', 'former', 'any', 'through', 'they', 'whole', 'becomes', 'around', 'yet', 'less', 'is', 'these', 'whatever', 'otherwise', 'as', 'anything', 'among', 'have', 'however', 'go', 'afterwards', 'since', 'still', 'can', 'beforehand', 'everywhere', 'why', 'seem', 'because', 'last', 'due', 'had', 'get', 'while', 'all', 'him', 'who', 'most', 'to', 'only', 'serious', 'meanwhile', 'are', 'show', 'several', 'at', 'might', 'onto', 'anyone', 'her', 'hereby', 'seemed', 'am', 'again', 'move', 'therein', 'than', 'did', 'very', 'it', 'anyhow', 'both', 'please', 'i', 'make', 'more', 'no', 'off', 'various', 'been', 'thereby', 'against', 'whence', 'third', 'there', 'ever', 'sometimes', 'every', 'take', 'we', 'say', 'each', 'also', 'what', 'me', 'us', 'anyway', 'none', 'per', 'thru', 'his', 'moreover', 'a', 'perhaps', 'how', 'yours', 'besides', 'whenever', 'empty', 'least', 'under', 'he', 'back', 'myself', 'namely', 'first', 'herself', 'into', 'someone', 'quite', 'never', 'always', 'here', 'via', 'cannot', 'must', 'ca', 'would', 'nevertheless', 'above', 'front', 'part', 'became', 'yourself', 'after', 'everything', 'your', 'somewhere', 'before', 'too', 'the', 'those', 'once', 'does', 'do', 'towards', 'could', 'keep', 'them', 'for', 'twenty', 'something', 'but', 'my', 'see', 'that', 'in', 'others', 'side', 'of', 'further', 'during', 'upon', 'behind', 'become', 'almost', 'whose', 'another', 'its', 'within', 'thereafter', 'bottom', 'whereas', 'when', 'seeming', 'just', 'either', 'put', 'or', 'call', 'being', 'be', 'fifty', 'beside', 'across', 'may', 'whereby', 'neither', 'was', 'rather', 'if', 'formerly', 'amongst', 'where', 'thus', 'ourselves', 'themselves', 'hence', 'ours']
    # custom stop words:
    stop_words += ['\'s', 'St.', 'tabu']
    for stop_word in stop_words:
        nlp.vocab[stop_word].is_stop = True

    print("loading up the prepared Annoy object...")
    vocab_forest = SimpleNeighbors.load('vocab_forest')

    return nlp

# Get vector for a string, which we assume is a single word.
def vector(w):
    if type(w) == str:
        vector = nlp(w)[0].vector
    elif type(w) == spacy.lexeme.Lexeme or spacy.tokens.token.Token:
        vector = w.vector
    else:
        vector = None
    return vector

def find_similar(target, count=20, offset=0):
    target_string = target

    if type(target) == str:
        target_vector = vector(target)
    elif type(target) == spacy.lexeme.Lexeme or spacy.tokens.token.Token:
        target_string = target.orth_
        target_vector = target.vector
    elif type(target) == numpy.ndarray:
        target_string = ''
        target_vector = target
    else:
        print("Invalid target for finding similar word by vector...")

    if vocab_forest.vec(target_string) != None:
        neighbors = vocab_forest.neighbors(target_string, offset+count)
    else:
        neighbors = vocab_forest.nearest(target_vector, offset+count)

    similar = list(n for n in neighbors if n.lower() != target_string.lower())[offset:offset+count]
    return similar

def mutation_candidates(tokens):
    return list(t for t in tokens if not (t.is_stop or t.is_punct))

def get_mutation_substitute(w):
    return choice(find_similar(w, offset=0, count=32))

def ok_to_tweet(m):
    # too long to tweet?
    if len(m) > 200:
        print("status is too long")
        return False
    # any bad words?
    elif wordfilter.blacklisted(m):
        print("found a bad word")
        return False
    else:
        return True

def mutate(motif, verbose=False, index=None):
    try:
        pieces      = motif.split()  # => ["A13.1.1", "Cow", "as", "creator."]
        index       = index or pieces[0]     # => "A13.1.1"
        body        = " ".join(pieces[1:])  # => "Cow as creator."
        tokens      = nlp(body)
        candidates  = mutation_candidates(tokens)

        if len(candidates) < 2:
            if verbose:
                print("Motif is not a good candidate for mutation:\n\t%s" % body)
            else:
                print(".", end=""); sys.stdout.flush();
            return None
        new_motif = body

        if verbose:
            print("Finding ~similar words for %s @ %s" % (candidates, datetime.datetime.time(datetime.datetime.now())))
        to_sub = list((c.orth_, get_mutation_substitute(c)) for c in candidates)

        for candidate,replacement in to_sub:
            if verbose:
                print("Replacing", candidate, "with", replacement)
            new_motif = re.sub(r"%s"%candidate, replacement, new_motif, count=1)

        index = index or motif.index
        if ok_to_tweet(new_motif) is False:
            if verbose:
                print("Mutated motif is not a good candidate to tweet:\n\t%s" % new_motif)
            return None
        new_motif = "%s %s" % (index, new_motif)
        if not verbose:
            print(".", end=""); sys.stdout.flush();
        return new_motif
    except:
        return None

def make_new_motifs(count=1, outfile=None, wipe=False, verbose=False, everything=False, offset=None, model=None, **kwargs):
    if everything:
        old_motifs = all_motifs
    elif offset is not None:
        print("offset: %s" % offset)
        print("count: %s" % count)
        old_motifs = all_motifs[offset:offset+count]
    else:
        old_motifs = sample(all_motifs, count)

    new_motifs = list(mutate(m, verbose) for m in old_motifs)

    # remove bad motifs:
    for i,m in enumerate(new_motifs):
        if m is None:
            old_motifs[i] = None
    old_motifs = list(filter(None, old_motifs))
    new_motifs = list(filter(None, new_motifs))

    transforms = list("'%s' \n\t=> '%s'" % (old_motifs[i], n) for i,n in enumerate(new_motifs) if n)
    if verbose:
        for t in transforms:
            print(t)

    if outfile:
        with open(outfile, 'w' if wipe else 'a', encoding="utf-8") as f:
            f.write("\n".join(new_motifs))

    return new_motifs

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Mutate lines using SpaCy")
    parser.add_argument("-o", "--outfile", type=str, default="new_motifs.txt",
            help="append to given file")
    parser.add_argument("-i", "--infile", type=str, default="motifs.txt",
            help="readlines from given file")
    parser.add_argument("-c", "--count", type=int, default=1,
            help="generate this many mutated motifs")
    parser.add_argument("-s", "--start", type=int, default=None, dest='offset',
            help="offset to work from in motif file")
    parser.add_argument("-v", "--verbose", action="store_true",
            help="verbose stdout printing")
    parser.add_argument("-w", "--wipe", action="store_true",
            help="wipe out contents of outfile instead of appending")
    parser.add_argument("-m", "--model", type=str, default='en_vectors_web_lg',
            help="which SpaCy model to load (default: en_vectors_web_lg)")
    parser.add_argument("-e", "--everything", action="store_true",
            help="Run through every line from infile, not a random sample.")
    args = parser.parse_args()

    if args.verbose:
        print("Mutating %s motifs from %s and %swriting out to %s" % ("ALL" if args.everything else args.count, args.infile, "OVER" if args.wipe else "",args.outfile))
    else:
        print("Mutating %s motifs..." % "ALL" if args.everything else args.count)

    all_motifs = populate_motifs(args.infile)

    print("Loading spacy parser...")
    nlp = init_nlp(model=args.model)

    print("Making motifs:")
    make_new_motifs(**vars(args))
