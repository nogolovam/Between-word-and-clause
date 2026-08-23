import pickle


def load_treebank(filename):
    """opens conllu file, loads data and returns a treebank data structure"""

    a_treebank = Treebank()
    a_sentence = None

    with open(filename, mode='r', encoding='utf-8') as data:
        for line in data:
            if line.startswith('# sent_id'):  # sentence identification
                a_sentence = Sentence()
                a_sentence.id = line.split('=')[1].strip()
                a_treebank.sentence_list.append(a_sentence)
            if line.startswith('# text ='):  # text identification
                #a_sentence.text = line.strip()
                a_sentence.text = line[len('# text = '):].strip()
            if not line.startswith('#') and len(line) > 1:# reads LF character too
                text = line.split('\t')
                if text[0].find('-') == -1:
                    a_sentence.word_list.append(create_worddata(line))
                    a_sentence.check_kompozita()
                    a_sentence.check_root()
                    a_sentence.make_filtr()
                    a_sentence.get_strings_sent()
                    a_sentence.get_vector()
                    a_sentence.make_word_no_punct()


    a_treebank.assign_next_node()
    a_treebank.find_parent_and_children()
    a_treebank.find_all_children()
    a_treebank.check_predicate()
    a_treebank.assign_new_id()
    a_treebank.run_all_functions()
    a_treebank.tag_units()
    a_treebank.count_sentences()
    a_treebank.count_units()

    return a_treebank

def add_word_to_all_parents(word, parent):
    """adds a word to all their parents from the bottom to top of the treebank data structure"""

    if parent is not None:
        parent.all_children.append(word)
        add_word_to_all_parents(word, parent.parent)


def list_non_clausal_children(direct_children, word_comment):
    """recursively creates a list of all children (==nodes) which do not belong to other clauses (==CUTS)"""

    clause_words = []

    if word_comment == "clause":
        for child in direct_children:
            if child.comment not in {"clause", "main_clause"}:
                clause_words.append(child)
                clause_words += list_non_clausal_children(child.direct_children, word_comment)

    if word_comment == "main_clause":
        for child in direct_children:
            if child.comment != "main_clause":
                clause_words.append(child)
                clause_words += list_non_clausal_children(child.direct_children, word_comment)

    return clause_words


def stringify_non_clausal_children(direct_children, word_comment):
    """recursively creates a string of all children which do not belong to other clauses (==CUTS)"""

    clause_words = ""

    if word_comment == "clause":

        for child in direct_children:
            if child.comment not in {"clause", "main_clause"}:
                clause_words += child.form + " "
                clause_words += stringify_non_clausal_children(child.direct_children, word_comment)
    #print(clause_words)

    if word_comment == "main_clause":

        for child in direct_children:
            if child.comment != "main_clause":
                clause_words += child.form + " "
                clause_words += stringify_non_clausal_children(child.direct_children, word_comment)

    return clause_words


def process_big_chunk_phrase(a_phrase_head, list_of_nodes):
    """llb when you go to the most left"""

    clausal_big_chunk = []
    current_big_chunk = []
    clausal_nodes = list_of_nodes

    # if a clausal head is the only clausal node
    if len(clausal_nodes) == 0:
        current_big_chunk.append(a_phrase_head)
        clausal_big_chunk.append(current_big_chunk)
        #print("clausal_nodes", clausal_llb)
        return clausal_big_chunk

    #print("id_word", id_word)
    #print("h_distance", h_distance)

    processed = []

    for i in range(len(clausal_nodes) - 1):

        current_node = clausal_nodes[i]
        #print("Current_node", current_node.form)
        if current_node not in processed:
            # if a next node. parent id == current node id and next_node.h_distnace == current_node.h_distance + 1
            if current_node.id == clausal_nodes[i + 1].parentID and clausal_nodes[i + 1].h_distance == current_node.h_distance + 1:
                current_big_chunk.append(clausal_nodes[i])
                processed.append(clausal_nodes[i])
                #current_llb.append(clausal_nodes[i + 1])
                #processed.append(clausal_nodes[i + 1])
                #print("Processed", processed)
            # none of the conditions applies -> close a segment
            else:
                current_big_chunk.append(clausal_nodes[i])
                processed.append(clausal_nodes[i])
                clausal_big_chunk.append(current_big_chunk)
                #print("Processed_else", processed)
                #print("clausal_nodes", clausal_llb)
                current_big_chunk = []
        else:
            continue

    # processes the last node of the clause (==renegade)
    if clausal_nodes[-1] not in processed:
        current_big_chunk.append(clausal_nodes[-1])

    clausal_big_chunk.append(current_big_chunk)
    #print("clausal_nodes", clausal_llb)

    return clausal_big_chunk

def save_treebank(treebank, filename):

    with open(filename, 'wb') as file:
        pickle.dump(treebank, file)

    del treebank

    print(f"Treebank saved to {filename}")


def load_treebank_pkl(filename):

    with open(filename, 'rb') as file:
        treebank = pickle.load(file)
    print(f"Treebank loaded from {filename}")

    return treebank


class Treebank:

    def __init__(self):
        self.sentence_list: list[Sentence()] = []
        self.n_s_jen_conj = 0
        self.n_s_jen_conj_a_coord = 0
        self.n_s_bez_conj = 0
        self.n_s_bez_conj_a_coord = 0
        self.n_s_jen_filtr = 0
        self.all_s = 0

    def assign_next_node(self):
        """adds a next node to word data"""

        for sentence in self.sentence_list:
            #print(sentence)
            for i in range(len(sentence.word_list) - 1):
                sentence.word_list[i].next_node = sentence.word_list[i + 1]

                if (sentence.word_list[i].id + 1) != sentence.word_list[i + 1].id:
                    raise ValueError('ERROR!')

    def find_parent_and_children(self):  # NOTE: root parent is None!
        """interlinks the data based on the parent-child relationship"""

        for sentence in self.sentence_list:
            for word in sentence.word_list:
                if word.parentID != 0 and word.deprel != 'punct' and word.parentID is not None and not word.punct:
                    word.parent = sentence.word_list[word.parentID - 1]  # assign a parent in the form of a word class
                    word.parent.direct_children.append(word)  # add a child to its parent
                else:
                    sentence.root = word

                if word.deprel == 'root':
                    sentence.root_f_h = word

    def find_all_children(self):
        """finds all nodes directly and indirectly dependent on a given word in the treebank data structure"""

        for sentence in self.sentence_list:
            for word in sentence.word_list:
                if word.deprel != 'punct' and not word.punct:
                    add_word_to_all_parents(word, word.parent)


    def tag_units(self):

        for sentence in self.sentence_list:
            sentence.identify_main_clause_words()
            for main_clause in sentence.main_clause_list:
                main_clause.identify_clause_words()
            #for clause in main_clause.clause_list:
                #clause.MDD_clause_get()
                #clause.get_LDS()
                #clause.get_subj_part()
                #clause.get_word_form_bez_subj()
                #clause.get_phrase()

    def count_sentences(self):

        for sentence in self.sentence_list:
            sentence.get_num_conj()
            self.all_s += 1

            if sentence.root_good and sentence.coordination and not sentence.bad_things:
                self.n_s_jen_conj += 1

            if sentence.root_good and (sentence.coordination or sentence.kompozita) and not sentence.bad_things:
                self.n_s_jen_conj_a_coord += 1

            if sentence.root_good and not sentence.coordination and not sentence.bad_things:
                self.n_s_bez_conj += 1

            if sentence.root_good and not sentence.coordination and not sentence.kompozita and not sentence.bad_things:
                self.n_s_bez_conj_a_coord += 1

            if sentence.root_good and not sentence.bad_things:
                self.n_s_jen_filtr += 1

    def run_all_functions(self):
        for sentence in self.sentence_list:
            for word in sentence.word_list:
                if word.deprel != "root" and word.deprel != "punct" and word.parentID is not None:
                    try:
                        word.distance = abs(word.parent.new_id - word.new_id)
                    except AttributeError:
                        print(
                            f"Something wrong with parent. Sentence, id:{sentence.id}, sentence {sentence.word_form}, word: {word.form}")
            sentence.get_h_distance()
            sentence.MDD_MHD_sentence_get()
            for main_clause in sentence.main_clause_list:
                for clause in main_clause.clause_list:
                    clause.MDD_clause_get()

    def check_predicate(self):
        for sentence in self.sentence_list:
            for word in sentence.word_list:
                if word.deprel == 'root' and word.upos in {'VERB', 'AUX'} and word.xpos[:2] != 'Vf':
                    word.check_recursively()

    def assign_new_id(self):

        for sentence in self.sentence_list:
            for word in sentence.word_list:
                if word.next_node is not None and word.upos == 'PUNCT':
                    word.next_node.new_id = word.new_id

                if word.next_node is not None and word.upos != 'PUNCT' and word.next_node.new_id != word.new_id + 1:
                    word.next_node.new_id = word.new_id + 1

    def count_units(self):
        for sentence in self.sentence_list:
            sentence.length_by_main_clause = 0
            sentence.length_by_clause = 0
            sentence.length_by_phrase = 0
            sentence.length_by_big_chunk = 0
            sentence.length_by_chunk = 0

            for mainclause in sentence.main_clause_list:
                sentence.length_by_main_clause += 1
                mainclause.length_by_clause = 0
                mainclause.length_by_phrase = 0
                mainclause.length_by_big_chunk = 0
                mainclause.length_by_chunk = 0

                for clause in mainclause.clause_list:
                    sentence.length_by_clause += 1
                    mainclause.length_by_clause += 1
                    clause.length_by_phrase = 0
                    clause.length_by_big_chunk = 0
                    clause.length_by_chunk = 0

                    for phrase in clause.phrase_list:
                        sentence.length_by_phrase += 1
                        mainclause.length_by_phrase += 1
                        clause.length_by_phrase += 1
                        phrase.length_by_big_chunk = 0
                        phrase.length_by_chunk = 0
                        phrase.length_by_chunk2 = 0

                        for big_chunk in phrase.big_chunk_list:
                            sentence.length_by_big_chunk += 1
                            mainclause.length_by_big_chunk += 1
                            clause.length_by_big_chunk += 1
                            phrase.length_by_big_chunk += 1
                            big_chunk.length_by_chunk = 0

                            for chunk in big_chunk.chunk_list:
                                sentence.length_by_chunk += 1
                                mainclause.length_by_chunk += 1
                                clause.length_by_chunk += 1
                                phrase.length_by_chunk += 1
                                big_chunk.length_by_chunk += 1

                            for chunk2 in big_chunk.chunk2_list:
                                big_chunk.length_by_chunk2 += 1

class Sentence:

    def __init__(self):
        self.id = None
        self.text = None
        self.word_form = None
        self.lemma = None
        self.root = None
        self.word_list: list[Word()] = []
        self.MDD_sentence = 0
        self.num_depend_word = 0
        self.sum_of_DD = 0
        self.main_clause_list: list[MainClause()] = []
        self.length_by_main_clause = 0
        self.length_by_clause = 0
        self.length_by_phrase = 0
        self.length_by_big_chunk = 0
        self.length_by_chunk = 0
        self.length_by_word = 0
        self.coordination = False #všechna
        self.chosen_punct = False
        self.zavorka = False
        self.zkratka = False
        self.num = False
        self.cizi_slova = False
        self.kompozita = False
        self.root_good = False
        self.condicional = False
        self.bad_things = False
        self.bad_things2 = False #bad_things + uvozovky + condicional
        self.MHD_sentence = 0
        self.sum_of_HD = 0
        self.num_depend_word_h = 0
        self.root_f_h = None
        self.vector = []
        self.word_list_no_punct = []
        self.clause_coordination = False
        self.num_conj = 0 #nepočítám conj clause, taking the biggest list of conj

    def identify_main_clause_words(self):

            for word in self.word_list:
                if word.comment == 'main_clause':
                    #print(word.form)
                    main_clause_words_form = stringify_non_clausal_children(word.direct_children, word.comment)
                    #print(clause_words_form)
                    main_clause_words_form += word.form
                    main_clause_nodes = list_non_clausal_children(word.direct_children, word.comment)
                    main_clause_nodes.append(word)
                    new_main_clause = MainClause()
                    new_main_clause.word_list = main_clause_nodes
                    new_main_clause.clause_form = main_clause_words_form
                    new_main_clause.get_strings_main_clause()
                    new_main_clause.get_vector_id()
                    new_main_clause.sentence_id = self.id
                    self.main_clause_list.append(new_main_clause)
                    #self.length_by_main_clause = len(self.main_clause_list)

    def get_strings_sent(self):

        word_forms = []
        lemma = []

        for word in self.word_list:
            if word.deprel != "punct" and not word.punct:
                word_forms.append(word.form)
                lemma.append(word.lemma)


        self.word_form = " ".join(word_forms)
        self.lemma = " ".join(lemma)

        #print(f"Sentence string made: {self.text}, {self.id}")


    def MDD_MHD_sentence_get(self):
        hodnoty = []
        hodnoty_h = []
        for word in self.word_list:
            if word.deprel != "root" and word.deprel != "punct" and not word.punct:
                hodnoty.append(word.distance)
                hodnoty_h.append(word.h_distance)

        if len(hodnoty) != 0:
            self.MDD_sentence = sum(hodnoty) / len(hodnoty)
            self.num_depend_word = len(hodnoty)
            self.sum_of_DD = sum(hodnoty)

        if len(hodnoty_h) != 0:
            self.MHD_sentence = sum(hodnoty_h) / len(hodnoty_h)
            self.num_depend_word_h = len(hodnoty_h)
            self.sum_of_HD = sum(hodnoty_h)

    def get_h_distance(self):
        if self.root_f_h is not None:
            self.root.h_distance = 0  # Initialize the h_distance for the root word
            self.get_h_distance_recursive(self.root_f_h)
        else:
            print("No root found for the sentence.")
            print(self.text)

    def get_h_distance_recursive(self, a_word):
        for child in a_word.direct_children:
            #print(a_word.form)
            if child.upos != "PUNCT" and not child.punct:
                child.h_distance = a_word.h_distance + 1
                self.get_h_distance_recursive(child)

    def make_filtr(self):
        unwanted_lemmas = {
            '(', ')', '#', '$', '%', '&', '*', '+', '/', '<', '=', '>', '@', '[', '\\', ']', '^', '_', '`',
            '{', '|', '}', '~', '£', '§', '¨', '©', '«', '®', '°', '±', '²', '´', 'µ', '»', '¼', '½', '¾',
            '¿', '×', 'ß', '÷', 'ø', 'ɪ', 'ʼ', 'ˆ', 'ˇ', '˘', '͡', 'β', 'γ', 'δ', 'κ', 'λ', 'μ', 'π', 'ρ',
            'σ', 'ϵ', 'б', 'г', 'и', 'й', 'л', 'м', 'т', 'у', 'ы', 'х', 'я', 'ѐ', 'ә', 'ồ', '†', '•', '‰',
            '‹', '›', '€', '™', '→', '↩', '∈', '∆', '∗', '∙', '≈', '≠', '≥', '■', '□', '▪', '▲', '●', '♂',
            '✳', '⟶', 'ﬁ', '…', 'x', 'h', 'n', 'ř', 't', 'eagle', 'c', 'cz', 'm', 'ch', 'ž', 'j', 'b-29', 'C',
        }

        bad_one = {'ä', 'ö', 'ü'}
        if "..." in self.text:
            self.bad_things = True
            self.bad_things2 = True

        for word in self.word_list:
            if word.deprel in {'conj', 'appos', 'conj@emb', 'conj:dicto', 'conj:coord', 'conj:appos'}:
                self.coordination = True
            if word.deprel == "punct" and (word.lemma == '"' or word.lemma == '(' or word.lemma == ')'):
                self.chosen_punct = True
            if word.deprel == "punct" and (word.lemma == '(' or word.lemma == ')'):
                self.zavorka = True
            if word.feats.startswith("Abbr=Yes"):
                self.zkratka = True
            if word.upos == "NUM":
                self.num = True
            if word.feats.startswith("Foreign=Yes"):
                self.cizi_slova = True
            if word.feats.startswith("Mood=Cnd"):
                self.condicional = True
            if (
                    (word.deprel == "punct" and word.lemma in {'(', ')'})
                    or word.deprel == "unk"
                    or word.feats.startswith("Abbr=Yes")
                    or word.upos == "NUM"
                    or word.feats.startswith("Foreign=Yes")
                    or (word.upos == 'PUNCT' and word.deprel != 'punct')
                    or (word.deprel == 'punct' and word.upos != 'PUNCT')
                    or word.lemma in unwanted_lemmas
                    or word.deprel == 'flat'
                    or word.deprel == 'orphan'
                    or (word.upos == 'PROPN' and any(char in bad_one for char in word.form))
                    or (word.form == 'm' and word.lemma == 'metr')
            ):
                self.bad_things = True
            if (
                    (word.deprel == "punct" and word.lemma in {'(', ')'})
                    or word.deprel == "unk"
                    or word.feats.startswith("Abbr=Yes")
                    or word.upos == "NUM"
                    or word.feats.startswith("Foreign=Yes")
                    or (word.upos == 'PUNCT' and word.deprel != 'punct')
                    or (word.deprel == 'punct' and word.upos != 'PUNCT')
                    or word.lemma in unwanted_lemmas
                    or word.feats.startswith("Mood=Cnd")
                    or (word.deprel == "punct" and word.lemma == '"')
                    or (word.deprel == "punct" and word.lemma == '–')
                    or word.deprel == 'flat'
                    or word.deprel == 'orphan'
            ):
                self.bad_things2 = True
            if word.deprel == 'conj' and word.parent is not None and (word.parent.upos == 'VERB' or word.parent.upos == 'AUX') and word.parent.xpos[0:2] != 'Vf':
                if (word.upos == 'VERB' or word.upos == 'AUX') and word.xpos[0:2] != 'Vf':
                    self.clause_coordination = True
            if word.parent is not None and word.parent.parent is not None:
                if (word.parent.upos == 'CCONJ' or (word.parent.deprel == 'conj' and word.parent.upos != 'SCONJ')) and (word.parent.parent.upos == 'VERB' or word.parent.parent.upos == 'AUX') and word.parent.parent.xpos[0:2] != 'Vf':
                    if (word.upos == "VERB" or word.upos == "AUX") and word.xpos[0:2] != "Vf" and word.deprel != 'comp:aux':
                        self.clause_coordination = True
            if word.parent is not None and word.parent.parent is not None:
                if word.deprel == 'conj' and word.upos == "VERB" and word.xpos[0:2] != "Vf":
                    if word.parent.upos == "ADJ" and word.parent.parent.upos == "AUX" and word.parent.parent.xpos[0:2] != "Vf":
                        self.clause_coordination = True
                    elif word.parent.upos == "NOUN" and word.parent.parent.upos == "AUX" and word.parent.parent.xpos[0:2] != "Vf":
                        self.clause_coordination = True
            if word.parent is not None:
                if (word.parent.upos == 'SCONJ' and word.parent.deprel != 'root') and (word.upos == 'VERB' or word.upos == 'AUX') and word.xpos[0:2] != 'Vf' and word.deprel == 'conj':
                    self.clause_coordination = True
            if word.parent is not None:
                if word.parent.deprel == 'conj' and (word.parent.upos == "VERB" or word.parent.upos == "AUX") and word.parent.xpos[0:2] != 'Vf':
                    if (word.upos == "VERB" or word.upos == "AUX") and word.xpos[0:2] != "Vf" and word.deprel == 'conj@emb':
                        self.clause_coordination = True

    def check_kompozita(self):
        with open('C:/Users/nogol/Documents/Doktorat/Analyzy/SUD/vysledky260403/MAL/kompozita_txt.txt', encoding="UTF-8", mode='r') as soubor:
            for radek in soubor:
                slova = radek.split(" ")

        for word in self.word_list:
            if word in slova:
                self.kompozita = True

    def check_root(self):

        for word in self.word_list:
            if word.deprel == 'root' and (word.upos == 'VERB' or word.upos == 'AUX') and word.xpos[0:2] != 'Vf':
                self.root_good = True

    def get_vector(self):

        vector_help = []
        for word in self.word_list:
            vector_help.append(word.parentID)

        self.vector = vector_help
        #print(self.vector)

    def make_word_no_punct(self):
        self.word_list_no_punct = []
        for word in self.word_list:
            if word.upos != "PUNCT" and not word.punct:
                self.word_list_no_punct.append(word)

    def get_num_conj(self):
        self.num_conj = 0  # Reset counter before new computation

        def get_num_conj_recursive(word, count):
            # Update max count
            self.num_conj = max(self.num_conj, count)

            for child in word.direct_children:
                if child.comment != 'main_clause' and child.deprel in {'conj', 'appos', 'conj@emb', 'conj:dicto', 'conj:coord', 'conj:appos'}:
                    get_num_conj_recursive(child, count + 1)

        for word in self.word_list:
            if word.comment != 'main_clause' and word.deprel in {'conj', 'appos', 'conj@emb', 'conj:dicto', 'conj:coord', 'conj:appos'}:
                get_num_conj_recursive(word, 1)

    def __repr__(self):
        return self.word_form

class MainClause:
    def __init__(self):
        self.word_list: list[Word()] = []
        self.clause_list: list[Clause()] = []
        self.length_by_clause = 0
        self.length_by_phrase = 0
        self.length_by_big_chunk = 0
        self.length_by_chunk = 0
        self.length_by_word = 0
        self.MDD_clause = 0
        self.clause_form = []
        self.word_form = None
        self.lemma = None
        self.vector_id = []
        self.highest_id = None
        self.sentence_id = None


    def get_strings_main_clause(self):

        word_forms = []
        lemma = []

        for word in self.word_list:
            if word.deprel != "punct" and not word.punct:
                word_forms.append(word.form)
                lemma.append(word.lemma)


        self.word_form = " ".join(word_forms)
        self.lemma = " ".join(lemma)

        #print("Clause string made.")

    def get_vector_id(self):
        vector_help = []
        for word in self.word_list:
            vector_help.append(word.id)

        vector_help.sort()
        self.vector_id = vector_help
        self.highest_id = vector_help[-1]

    def identify_clause_words(self):

        for word in self.word_list:
            if word.comment in {'clause', 'main_clause'}:
                clause_words_form = stringify_non_clausal_children(word.direct_children, 'clause')
                #print(clause_words_form)
                clause_words_form += word.form
                clause_nodes = list_non_clausal_children(word.direct_children, 'clause')
                clause_nodes.append(word)
                new_clause = Clause()
                new_clause.word_list = clause_nodes
                new_clause.clause_form = clause_words_form
                new_clause.get_strings_clause()
                new_clause.get_left_part()
                new_clause.get_word_form_bez_left()
                new_clause.get_phrase()
                new_clause.sentence_id = self.sentence_id
                self.clause_list.append(new_clause)
                #self.length_by_clause = len(self.clause_list)
                new_clause.root_f_h_cl = word
                new_clause.root = word
                new_clause.get_h_distance()

    def __repr__(self):
        return self.word_form

class Clause:

    def __init__(self):
        self.word_list: list[Word()] = []
        self.clause_form = []
        self.word_form = None
        self.lemma = None
        self.vector_id = []
        self.highest_id = None
        self.max_HD_word = None
        self.min_HD_word = None
        self.phrase_list: list[Phrase()] = []
        self.length_by_phrase = 0
        self.length_by_big_chunk = 0
        self.length_by_chunk = 0
        self.length_by_word = 0
        self.left_part = []
        self.left_part_word_form = None
        self.clause_bez_left = []
        self.clause_bez_left_word_form = None
        self.sentence_id = None
        self.MDD_clause = 0
        self.num_depend_word = 0
        self.sum_of_DD = 0
        self.root_f_h_cl = None
        self.root = None

    def get_strings_clause(self):

        word_forms = []
        lemma = []

        for word in self.word_list:
            if word.deprel != "punct" and not word.punct:
                word_forms.append(word.form)
                lemma.append(word.lemma)


        self.word_form = " ".join(word_forms)
        self.lemma = " ".join(lemma)

        #print("Clause string made.")
    def get_left_part(self):

        self.left_part = []
        word_form_left = []
        proceed = []
        clausal_nodes = self.word_list.copy()
        clausal_nodes.sort(key=lambda word_node: word_node.h_distance)
        #print("clausal nodes: ", clausal_nodes)

        predicate_id = None

        for word in clausal_nodes:
            if (word.comment in {'clause', 'main_clause'} and word.upos != 'SCONJ') or word.comment == 'predicate_in_sconj':
                predicate_id = word.id
                #print("predicate: ", word)


        # for word in self.word_list:
        word_id = 0
        third = False
        while not third and word_id < len(clausal_nodes):
            word = clausal_nodes[word_id]
            if word.comment in {'clause', 'main_clause'} and word.upos == 'SCONJ' and word not in proceed:
                self.left_part.append(word)
                proceed.append(word)
                self.add_all_children(word, proceed)
                break
            first = word.comment not in {'clause', 'main_clause'} and word.upos != 'SCONJ'
            second = word.comment != 'predicate_in_sconj'
            third = first and second
            if word.parent is not None and predicate_id is not None:
                #print("word: " + word.form, ", parent: " + word.parent.form, ", comment: ", word.comment, ", parent_comment: ", word.parent.comment)
                if third and word not in proceed and word.parent.id == predicate_id:
                    #print(word)
                    self.left_part.append(word)
                    #print("subj_part: " + word.form)
                    for child in word.all_children:
                        if child in self.word_list and child not in proceed:
                            self.left_part.append(child)
                            proceed.append(child)
            word_id += 1

        for word in self.word_list:
            if ((word.comment in {'clause', 'main_clause'} and word.upos != 'SCONJ') or word.comment == 'predicate_in_sconj') and word not in proceed:
                self.left_part.append(word)
        #print('left, phrase:', self.left_part)

        for word in self.left_part:
            word_form_left.append(word.form)

        if len(word_form_left) != 0:
            self.left_part_word_form = " ".join(word_form_left)

        #print("subj_part :", self.subj_part_word_form)

    def add_all_children(self, word, proceed):

        for child in word.direct_children:
            #print("child_comment", child, child.comment)
            if (child.comment not in {'clause', 'main_clause'} and child.upos != 'SCONJ') and child.comment != 'predicate_in_sconj' and child not in proceed and child in self.word_list:
                #print("child_comment_after_condition", child, child.comment)
                self.left_part.append(child)
                proceed.append(child)
                self.add_all_children(child, proceed)

    def get_word_form_bez_left(self):

            word_form_bez_left = []
            self.clause_bez_left = []

            for word in self.word_list:
                if word not in self.left_part:
                    word_form_bez_left.append(word.form)
                    self.clause_bez_left.append(word)

            self.clause_bez_left_word_form = " ".join(word_form_bez_left)


    def get_phrase(self):

        processed_words = []


        #print("phrase with root: ")
        try:
            new_phrase = Phrase()
            new_phrase.word_list = self.left_part.copy()
            processed_words = self.left_part.copy()
            new_phrase.get_strings_phrase()
            new_phrase.get_root_word()
            new_phrase.get_HD_values()
            new_phrase.get_direct_children()
            new_phrase.get_big_chunk()
            self.phrase_list.append(new_phrase)
            #self.length_by_phrase = len(self.phrase_list)
        except ValueError:
            print(f"No left_part in the clause. {self.word_form}, {self.sentence_id}")
        #for phrase_word in new_phrase.word_list:
            #print(phrase_word.form)
        #print("#########")

        for word in self.clause_bez_left:
            if word not in processed_words and word.parent not in processed_words and word.parent in self.clause_bez_left:
                new_phrase = Phrase()
                new_phrase.word_list.append(word)
                processed_words.append(word)
                new_phrase.word_list.append(word.parent)
                processed_words.append(word.parent)

                # Collect all children of the word in the same clause
                to_process = word.direct_children.copy()  # Queue of children to process
                while to_process:
                    child = to_process.pop(0)
                    if child in self.clause_bez_left and child not in processed_words:
                        new_phrase.word_list.append(child)
                        processed_words.append(child)
                        to_process.extend(child.direct_children)  # Add grandchildren, etc,

                # Finalize the phrase and append it to the list
                new_phrase.get_strings_phrase()
                new_phrase.get_root_word()
                new_phrase.get_HD_values()
                new_phrase.get_direct_children()
                new_phrase.get_big_chunk()

                self.phrase_list.append(new_phrase)
                #self.length_by_phrase = len(self.phrase_list)
                #for phrase_word in new_phrase.word_list:
                    #print (phrase_word.form)
                #print("#########")

            elif word not in processed_words:
                new_phrase = Phrase()
                new_phrase.word_list.append(word)
                processed_words.append(word)


                # Collect all children of the word in the same clause
                to_process = word.direct_children.copy()  # Queue of children to process
                while to_process:
                    child = to_process.pop(0)
                    if child in self.clause_bez_left and child not in processed_words:
                        new_phrase.word_list.append(child)
                        processed_words.append(child)
                        to_process.extend(child.direct_children)  # Add grandchildren, etc.

                # Finalize the phrase and append it to the list
                new_phrase.get_strings_phrase()
                new_phrase.get_root_word()
                new_phrase.get_HD_values()
                new_phrase.get_direct_children()
                new_phrase.get_big_chunk()

                self.phrase_list.append(new_phrase)
                #self.length_by_phrase = len(self.phrase_list)

        #print("Phrase is made. ", self.sentence_id)

    def MDD_clause_get(self):
        hodnoty = []
        for word in self.word_list:
            if word.deprel != "root" and word.deprel != "punct" and not word.punct:
                hodnoty.append(word.distance)

        if len(hodnoty) != 0:
            self.MDD_clause = sum(hodnoty) / len(hodnoty)
            self.num_depend_word = len(hodnoty)
            self.sum_of_DD = sum(hodnoty)

    def get_h_distance(self):
        if self.root_f_h_cl is not None:
            self.root.h_distance_cl = 0  # Initialize the h_distance for the root word
            self.get_h_distance_recursive(self.root_f_h_cl)
        else:
            print("No root found for the clause.")
            print(self.word_form)

    def get_h_distance_recursive(self, a_word):
        for child in a_word.direct_children:
            #print(a_word.form)
            if child.upos != "PUNCT" and not child.punct and child in self.word_list:
                child.h_distance_cl = a_word.h_distance_cl + 1
                self.get_h_distance_recursive(child)

    def __repr__(self):
        return self.word_form

class Phrase:

    def __init__(self):
        self.word_list: list[Word()] = []
        self.deprel = ""
        self.word_form = ""
        self.lemma = ""
        self.root_phrase = None
        self.big_chunk_list: list[BigChunk()] = []
        self.max_HD_word = None
        self.min_HD_word = None
        self.length_by_big_chunk = 0
        self.direct_children = {}

    def get_strings_phrase(self):

        word_forms = []
        deprels = []
        lemma = []


        for word in self.word_list:
            word_forms.append(word.form)
            deprels.append(word.deprel)
            lemma.append(word.lemma)

        self.word_form = " ".join(word_forms)
        self.deprel = " ".join(deprels)
        self.lemma = " ".join(lemma)

    def get_root_word(self):

        HD = [word.h_distance for word in self.word_list if word.h_distance is not None]
        # print("HD phrase: ", self.word_form, HD)
        if HD:
            min_value = min(HD)
            for word in self.word_list:
                if word.h_distance == min_value:
                    self.root_phrase = word
                    #print(word.form)

    def get_HD_values(self):

        h_distance_values = []
        for word in self.word_list:
            if word.h_distance is not None:
                h_distance_values.append(word.h_distance)
        # print(h_distance_values)

        if len(h_distance_values) != 0:
            self.max_HD_word = max(h_distance_values)
            self.min_HD_word = min(h_distance_values)

        # print(self.min_HD_word, self.max_HD_word)

    def get_direct_children(self):

        self.direct_children = {}

        for word in self.word_list:
            if len(word.direct_children) != 0:
                for child in word.direct_children:
                    if child in self.word_list:
                        if word not in self.direct_children:
                            self.direct_children[word] = [child]
                        else:
                            self.direct_children[word].append(child)
                    if child not in self.word_list:
                        if word not in self.direct_children:
                            self.direct_children[word] = []
            else:
                if word not in self.direct_children:
                    self.direct_children[word] = []

        for word in self.word_list:
            if len(word.direct_children) != 0:
                for child in word.direct_children:
                    if child in self.word_list:
                        word.direct_children_phrase.append(child)
                for kid in word.all_children:
                    if kid in self.word_list:
                        word.all_children_phrase.append(kid)

        #print("Phrase self.direct_children:", self.direct_children)

    def get_big_chunk(self):
        processed_words = set()
        processed_words2 = set()
        phrase_words = self.word_list.copy()
        phrase_words2 = self.word_list.copy()

        # Sort by h_distance (ascending)
        phrase_words.sort(key=lambda word_node: word_node.h_distance)
        phrase_words2.sort(key=lambda word_node: word_node.h_distance)

        for word in phrase_words:
            if word not in processed_words:
                # Create a new big chunk starting with the current word
                new_big_chunk = BigChunk()
                #print(f"Starting new big chunk with word: {word}")
                self._build_big_chunk(word, new_big_chunk, processed_words)

                # Add the completed big chunk to the list
                self.big_chunk_list.append(new_big_chunk)
                new_big_chunk.delka_big_chunk = len(new_big_chunk.word_list)


                new_big_chunk.get_strings_big_chunk()
                new_big_chunk.get_root_word()
                new_big_chunk.get_HD_values()
                new_big_chunk.get_direct_children()
                new_big_chunk.get_chunk()
                new_big_chunk.get_chunk2()

    def _build_big_chunk(self, word, big_chunk, processed_words):
        """Recursively build a big chunk from the given word."""
        """ Taking all the kids as long they do not have more than one kid"""
        big_chunk.word_list.append(word)
        processed_words.add(word)

        for child in word.direct_children_phrase:
            #print ("child: ", child)
            if child not in processed_words:
                if len(child.direct_children_phrase) <= 1:
                    self._build_big_chunk(child, big_chunk, processed_words)
    #print("Phrase string made.")

    def __repr__(self):
        return self.word_form

class BigChunk:

    def __init__(self):
        self.word_list: list[Word()] = []
        self.delka_big_chunk = 0
        self.word_form = ""
        self.deprel = ""
        self.lemma = ""
        self.root_BigChunk= None
        self.chunk_list: list[Chunks()] = []
        self.chunk2_list: list[Chunks2()] = []
        self.max_HD_word = None
        self.min_HD_word = None
        self.length_by_chunk = 0
        self.length_by_chunk2 = 0
        self.length_by_word = 0
        self.direct_children = {}

    def get_strings_big_chunk(self):

        word_forms = []
        deprels = []
        lemma = []

        for word in self.word_list:
            word_forms.append(word.form)
            deprels.append(word.deprel)
            lemma.append(word.lemma)

        self.word_form = " ".join(word_forms)
        self.deprel = " ".join(deprels)
        self.lemma = " ".join(lemma)
        #print("LDS string made.")

    def get_root_word(self):

        HD = [word.h_distance for word in self.word_list if word.h_distance is not None]
        # print("HD phrase: ", self.word_form, HD)
        if HD:
            min_value = min(HD)
            for word in self.word_list:
                if word.h_distance == min_value:
                    self.root_BigChunk = word
                    #print(word.form)

    def get_direct_children(self):

        self.direct_children = {}

        for word in self.word_list:
            if len(word.direct_children) != 0:
                for child in word.direct_children:
                    if child in self.word_list:
                        if word not in self.direct_children:
                            self.direct_children[word] = [child]
                        else:
                            self.direct_children[word].append(child)
                    if child not in self.word_list:
                        if word not in self.direct_children:
                            self.direct_children[word] = []
            else:
                if word not in self.direct_children:
                    self.direct_children[word] = []

        for word in self.word_list:
            if len(word.direct_children) != 0:
                for child in word.direct_children:
                    if child in self.word_list:
                        word.direct_children_bigchunk.append(child)
                for kid in word.all_children:
                    if kid in self.word_list:
                        word.all_children_bigchunk.append(kid)

    def get_HD_values(self):

        h_distance_values = []
        for word in self.word_list:
            if word.h_distance is not None:
                h_distance_values.append(word.h_distance)
        # print(h_distance_values)

        if len(h_distance_values) != 0:
            self.max_HD_word = max(h_distance_values)
            self.min_HD_word = min(h_distance_values)

        # print(self.min_HD_word, self.max_HD_word)

    def get_chunk(self):
        processed_words = set()
        id_lds = [word.id for word in self.word_list]

        current_distance = self.max_HD_word
        while current_distance >= self.min_HD_word:
            words_at_distance = [word for word in self.word_list
                                 if word.h_distance == current_distance and word.id not in processed_words]

            parent_to_words = {}
            single_words = []

            for word in words_at_distance:
                if word.parent and word.parent.id in id_lds:
                    parent_id = word.parent.id
                    if parent_id not in parent_to_words:
                        parent_to_words[parent_id] = [word.parent]
                    parent_to_words[parent_id].append(word)
                else:
                    single_words.append(word)

            for parent_id, words in parent_to_words.items():
                # The first word is the chunk parent, separate from the rest for checking
                chunk_parent = words[0]
                valid_words = [chunk_parent]  # Always include the parent

                # Separate non-parent words that have children outside the chunk
                for word in words[1:]:  # Skip the parent (words[0])
                    # Check if the word has any children outside this chunk
                    children_outside_chunk = any(
                        child.id in id_lds and child.id in processed_words and child not in words
                        for child in word.direct_children
                    )
                    if children_outside_chunk:
                        # If the word has external children, add it as a single-word chunk
                        single_words.append(word)
                    else:

                        # If the word does not have external children, add it to the chunk
                        valid_words.append(word)

                #check if words in valid_words are linear neighbours in the sentence
                valid_words.sort(key=lambda word_node: word_node.new_id)
                delete_words = []
                for i in range(len(valid_words) - 1):
                    if valid_words[i].new_id + 1 != valid_words[i + 1].new_id:
                        #print(valid_words[i + 1])
                        delete_words.append(valid_words[i + 1])

                for word in delete_words:
                    valid_words.remove(word)
                    single_words.append(word)

                # Create chunk if valid_words contains more than just the parent
                if valid_words:
                    new_chunk = Chunks()
                    for word in valid_words:
                        if word.id not in processed_words:
                            new_chunk.word_list.append(word)
                            processed_words.add(word.id)

                    new_chunk.delka_chunk = len(new_chunk.word_list)
                    new_chunk.get_strings_chunk()
                    self.chunk_list.append(new_chunk)

            # Process remaining single words
            for word in single_words:
                if word.id not in processed_words:
                    new_chunk = Chunks()
                    new_chunk.word_list.append(word)
                    new_chunk.delka_chunk = 1
                    new_chunk.get_strings_chunk()
                    self.chunk_list.append(new_chunk)
                    processed_words.add(word.id)

            current_distance -= 1

        #self.length_by_chunk = len(self.chunk_list)

    def get_chunk2(self):
        processed_words = set()
        id_lds = [word.id for word in self.word_list]

        current_distance = self.max_HD_word
        while current_distance >= self.min_HD_word:
            words_at_distance = [word for word in self.word_list
                                 if word.h_distance == current_distance and word.id not in processed_words]

            parent_to_words = {}
            single_words = []

            for word in words_at_distance:
                if word.parent and word.parent.id in id_lds:
                    parent_id = word.parent.id
                    if parent_id not in parent_to_words:
                        parent_to_words[parent_id] = [word.parent]
                    parent_to_words[parent_id].append(word)
                else:
                    single_words.append(word)

            for parent_id, words in parent_to_words.items():
                # The first word is the chunk parent, separate from the rest for checking
                chunk_parent = words[0]
                valid_words = [chunk_parent]  # Always include the parent

                # Separate non-parent words that have children outside the chunk
                for word in words[1:]:  # Skip the parent (words[0])
                    # Check if the word has any children outside this chunk
                    children_outside_chunk = any(
                        child.id in id_lds and child.id in processed_words and child not in words
                        for child in word.direct_children
                    )
                    if children_outside_chunk:
                        # If the word has external children, add it as a single-word chunk
                        single_words.append(word)
                    else:

                        # If the word does not have external children, add it to the chunk
                        valid_words.append(word)

                # Create chunk if valid_words contains more than just the parent
                if valid_words:
                    new_chunk = Chunks2()
                    for word in valid_words:
                        if word.id not in processed_words:
                            new_chunk.word_list.append(word)
                            processed_words.add(word.id)

                    new_chunk.delka_chunk = len(new_chunk.word_list)
                    new_chunk.get_strings_chunk2()
                    self.chunk2_list.append(new_chunk)

            # Process remaining single words
            for word in single_words:
                if word.id not in processed_words:
                    new_chunk = Chunks2()
                    new_chunk.word_list.append(word)
                    new_chunk.delka_chunk = 1
                    new_chunk.get_strings_chunk2()
                    self.chunk2_list.append(new_chunk)
                    processed_words.add(word.id)

            current_distance -= 1

    def __repr__(self):
        return self.word_form


class Chunks:

    def __init__(self):
        self.chunks_id = []
        self.word_list: list[Word()] = []
        self.delka_chunk = 0
        self.word_form = ""
        self.deprel = ""
        self.lemma = ""

    def get_strings_chunk(self):
        word_forms = []
        deprels = []
        lemma = []

        for word in self.word_list:
            word_forms.append(word.form)
            deprels.append(word.deprel)
            lemma.append(word.lemma)

        self.word_form = " ".join(word_forms)
        self.deprel = " ".join(deprels)
        self.lemma = " ".join(lemma)

        #print("Chunk string made.")

    def __repr__(self):
        return self.word_form

class Chunks2:

    def __init__(self):
        self.chunks_id = []
        self.word_list: list[Word()] = []
        self.delka_chunk = 0
        self.word_form = ""
        self.deprel = ""
        self.lemma = ""

    def get_strings_chunk2(self):
        word_forms = []
        deprels = []
        lemma = []

        for word in self.word_list:
            word_forms.append(word.form)
            deprels.append(word.deprel)
            lemma.append(word.lemma)

        self.word_form = " ".join(word_forms)
        self.deprel = " ".join(deprels)
        self.lemma = " ".join(lemma)

        #print("Chunk string made.")

    def __repr__(self):
        return self.word_form

class Word:

    def __init__(self):
        self.id = None
        self.form = None
        self.lemma = None
        self.upos = None
        self.xpos = None
        self.feats = None
        self.parentID = None
        self.parent = None
        self.deprel = None
        self.deps = None
        self.transliteration = None
        self.comment = None
        self.next_node = None
        self.direct_children = []
        self.all_children = []
        self.distance = 0
        self.num_syllab = 0
        self.prepis_CV = None
        self.orig = None
        self.phoneme_word = None
        self.h_distance = 0
        self.h_distance_cl = 0
        self.num_syllab_lemma = 0
        self.direct_children_phrase = []
        self.all_children_phrase = []
        self.direct_children_bigchunk = []
        self.all_children_bigchunk = []
        self.direct_children_bigchunk2 = []
        self.all_children_bigchunk2 = []
        self.punct = False
        self.new_id = None

    def check_main_clause(self):
        """
        Consolidates all checks for determining whether a word belongs to a main clause.
        """
        # Root node is a main clause if it's a VERB or AUX and not infinitive (Vf)
        if self.deprel == 'root' and self.upos in {'VERB', 'AUX'} and self.xpos[:2] != 'Vf':
            self.comment = 'main_clause'


        # Conjunct verbs (direct children of the root/main clause)
        elif self.parent and self.parent.comment == 'main_clause':
            if self.upos in {'VERB', 'AUX'} and self.xpos[:2] != 'Vf' and self.deprel in {'conj', 'conj@emb'} and self.parent.upos != 'SCONJ':
                self.comment = 'main_clause'

        # Nested cases: parent is part of a main clause
        if self.parent and self.parent.parent and self.parent.parent.comment == 'main_clause':
            if self.upos in {'VERB', 'AUX'} and self.xpos[:2] != 'Vf' and self.deprel in {'conj', 'conj@emb'}:
                if self.parent.upos in {'ADJ', 'NOUN'} and self.parent.parent.upos in {'VERB', 'AUX'}:
                    self.comment = 'main_clause'

    def check_clause(self):
        """
        Consolidates all checks for determining whether a word belongs to a clause.
        """
        # Skip nodes already marked as 'main_clause'
        if self.comment == 'main_clause':
            return

        # Handle SCONJ with child predicates
        if self.upos == 'SCONJ' and self.deprel != 'conj@emb':
            for child in self.direct_children:
                if child.upos in {'VERB', 'AUX'} and child.xpos[:2] != 'Vf' and child.deprel != 'comp:aux':
                    self.comment = 'clause'
                    child.comment = 'predicate_in_sconj'

        elif self.parent:
            if self.parent.upos in {'NOUN', 'PROPN', 'ADJ', 'PRON'}:
                if self.upos in {'VERB', 'AUX'} and self.xpos[:2] != 'Vf':
                    self.comment = 'clause'
            elif self.parent.upos in {'VERB', 'AUX'} and self.parent.xpos[:2] != 'Vf' and self.parent.deprel not in {'comp:aux', 'comp:pred'}:
                if self.deprel not in {'comp:aux', 'comp:pred', 'conj'} and self.upos in {'VERB', 'AUX'} and self.xpos[:2] != 'Vf':
                    self.comment = 'clause'
            elif self.parent.upos == 'SCONJ' and self.parent.deprel != 'root':
                if self.upos in {'VERB', 'AUX'} and self.xpos[:2] != 'Vf' and self.deprel == 'conj':
                    self.comment = 'clause'
            elif self.parent.upos == 'DET':
                if self.deprel not in {'comp:aux', 'comp:pred'} and self.upos in {'VERB', 'AUX'} and self.xpos[:2] != 'Vf':
                    self.comment = 'clause'
            elif self.parent.upos in {'VERB', 'AUX'} and self.parent.xpos[:2] == 'Vf' and self.parent.deprel not in {'comp:aux', 'comp:pred'}:
                if self.deprel not in {'comp:aux', 'comp:pred', 'conj'} and self.upos in {'VERB', 'AUX'} and self.xpos[:2] != 'Vf':
                    self.comment = 'clause'
            elif self.deprel == 'conj' and self.parent.upos in {'VERB', 'AUX'} and self.parent.xpos[:2] != 'Vf':
                if self.upos in {'VERB', 'AUX'} and self.xpos[:2] != 'Vf':
                    self.comment = 'clause'

        if self.parent and self.parent.comment == 'clause':
            if self.upos in {'VERB', 'AUX'} and self.xpos[:2] != 'Vf' and self.deprel in {'conj', 'conj@emb'} and self.parent.upos != 'SCONJ':
                self.comment = 'clause'

        if self.parent and self.parent.comment == 'predicate_in_sconj':
            if self.upos in {'VERB', 'AUX'} and self.xpos[:2] != 'Vf' and self.deprel in {'conj', 'conj@emb'} and self.parent.upos != 'SCONJ':
                self.comment = 'clause'

    def apply_all_checks(self):
        """Apply all checks to the current node."""
        self.check_main_clause()
        self.check_clause()

    def check_recursively(self):
        """Apply checks to the current node and recursively to all children."""
        self.apply_all_checks()
        for child in self.direct_children:
            child.check_recursively()

    def __repr__(self):
        return self.form


def create_worddata(a_line):
    """processes data from a word line"""

    not_good = {'xxx', 'XXX', '´,', '”', '—', '‘', '’', '–', '´.'}

    new_word = Word()
    word_data = a_line.split('\t')
    new_word.id = int(word_data[0])
    new_word.form = str(word_data[1].strip()).lower()  # strip fc for arbitrary spaces #vždy bude malými písmeny
    if new_word.form in not_good:
        new_word.punct = True
    new_word.lemma = word_data[2]
    new_word.upos = word_data[3]
    new_word.xpos = word_data[4]
    new_word.feats = word_data[5]
    if word_data[6] != '_':
        new_word.parentID = int(word_data[6])
    else:
        new_word.parentID = None
    new_word.deprel = word_data[7]
    new_word.deps = word_data[8]
    new_word.new_id = int(word_data[0])
    #if new_word.deprel != "root" and new_word.deprel != "punct" and not new_word.punct and new_word.parentID is not None:
        #new_word.distance = abs(new_word.parentID - new_word.id)
    if 'Translit' in a_line:
        new_word.transliteration = word_data[9].split('=')[-1].strip().lower()  # strip fc for arbitrary spaces
    new_word.num_syllab = get_num_syllab(new_word.form)[0]
    new_word.prepis_CV = get_num_syllab(new_word.form)[1]
    new_word.orig = get_num_syllab(new_word.form)[2]
    new_word.phoneme_word = get_phoneme_word(new_word.form)
    new_word.num_syllab_lemma = get_num_syllab(new_word.lemma)[0]

    #print("Word is made.")

    return new_word


def get_num_syllab(word_form):
    pocet_slabik = 0
    orig = ""
    orig = word_form
    word_form_CV = ""
    word_form = word_form.replace("pouč", "po@uč")
    word_form = word_form.replace("nauč", "na@uč")
    word_form = word_form.replace("douč", "do@uč")
    word_form = word_form.replace("přeuč", "pře@uč")
    word_form = word_form.replace("přiuč", "při@uč")
    word_form = word_form.replace("vyuč", "vy@uč")
    word_form = word_form.replace("pouka", "po@uka")
    word_form = word_form.replace("pouká", "po@uká")
    word_form = word_form.replace("poukl", "po@ukl")
    word_form = word_form.replace("poulič", "po@ulič")
    word_form = word_form.replace("poum", "po@um")
    word_form = word_form.replace("poupr", "po@upr")
    word_form = word_form.replace("pouráž", "po@uráž")
    word_form = word_form.replace("pousm", "po@usm")
    word_form = word_form.replace("poust", "po@ust")
    word_form = word_form.replace("poute", "po@ute")
    word_form = word_form.replace("pouvaž", "po@uvaž")
    word_form = word_form.replace("pouzen", "po@uzen")
    word_form = word_form.replace("douč", "do@uč")
    word_form = word_form.replace("douprav", "do@uprav")
    word_form = word_form.replace("doužív", "do@užív")
    word_form = word_form.replace("douzov", "do@uzov")
    word_form = word_form.replace("doupřesn", "do@upřesn")
    word_form = word_form.replace("doudit", "do@udit")
    word_form = word_form.replace("doudí", "do@udí")
    word_form = word_form.replace("eufemism", "Efemism")
    word_form = word_form.replace("eufor", "Efor")
    word_form = word_form.replace("euro", "Ero")
    word_form = word_form.replace("eutan", "Etan")
    word_form = word_form.replace("farmaceut", "farmacEt")
    word_form = word_form.replace("feud", "fEd")
    word_form = word_form.replace("koloseu", "KolosE")
    word_form = word_form.replace("koreu", "korE")
    word_form = word_form.replace("leuk", "lEk")
    word_form = word_form.replace("linoleu", "linolE")
    word_form = word_form.replace("mauzoleu", "mauzolE")
    word_form = word_form.replace("muzeu", "muzE")
    word_form = word_form.replace("neutral", "nEtral")
    word_form = word_form.replace("neutrál", "nEtrál")
    word_form = word_form.replace("pneum", "pnEm")
    word_form = word_form.replace("pseudo", "psEdo")
    word_form = word_form.replace("terapeut", "terapEt")
    word_form = word_form.replace("eufon", "Efon")
    word_form = word_form.replace("eunuch", "Enuch")
    word_form = word_form.replace("eunuš", "Enuš")
    word_form = word_form.replace("zeugm", "zEgm")
    word_form = word_form.replace("jubileu", "jubilE")
    word_form = word_form.replace("eucken", "Ecken")
    word_form = word_form.replace("kreuzmann", "krEzmann")
    word_form = word_form.replace("pilocereus", "pilocerEs")
    word_form = word_form.replace("cephalocereus", "cephalocerEs")
    word_form = word_form.replace("ou", "O")
    word_form = word_form.replace("au", "A")
    vokaly = ["a", "á", "e", "é", "ě", "i", "í", "y", "ý", "o", "ó", "u", "ú", "ů", "E", "A", "O"]
    for vokal in vokaly:
        word_form = word_form.replace(vokal, "V")
    konsonanty = ["b", "c", "č", "d", "ď", "f", "g", "h", "k", "p", "ř", "s", "š", "t", "ť", "v", "w", "z", "ž"]
    for hlaska in konsonanty:
        word_form = word_form.replace(hlaska, "C")
    word_form = word_form.replace("CrC", "CVC")
    word_form = word_form.replace("ClC", "CVC")
    word_form = word_form.replace("CmC", "CVC")
    word_form = word_form.replace("CrV", "CCV")
    word_form = word_form.replace("ClV", "CCV")
    word_form = word_form.replace("CmV", "CCV")
    sonory = ["m", "n", "j", "ň"]
    for sonora in sonory:
        word_form = word_form.replace(sonora, "S")
    word_form = word_form.replace("SrS", "CVC")
    word_form = word_form.replace("SlS", "CVC")
    word_form = word_form.replace("SrC", "CVC")
    word_form = word_form.replace("SlC", "CVC")
    word_form = word_form.replace("CrS", "CVC")
    word_form = word_form.replace("ClS", "CVC")
    word_form = word_form.replace("SrV", "SCV")
    word_form = word_form.replace("SlV", "SCV")
    word_form = word_form.replace("Cr", "CV")
    word_form = word_form.replace("Cl", "CV")
    word_form = word_form.replace("Cm", "CV")
    word_form = word_form.replace("Sr", "CV")
    word_form = word_form.replace("Sl", "CV")
    word_form = word_form.replace("r", "S")
    word_form = word_form.replace("l", "S")
    word_form = word_form.replace("@", "")
    word_form_CV = word_form
    for hlaska in word_form:
        if hlaska == "V":
            pocet_slabik += 1

    return pocet_slabik, word_form_CV, orig


def get_phoneme_word(word_form):

    word_form = word_form
    word_form = word_form.replace("pouč", "po@uč")
    word_form = word_form.replace("nauč", "na@uč")
    word_form = word_form.replace("douč", "do@uč")
    word_form = word_form.replace("přeuč", "pře@uč")
    word_form = word_form.replace("přiuč", "při@uč")
    word_form = word_form.replace("vyuč", "vy@uč")
    word_form = word_form.replace("pouka", "po@uka")
    word_form = word_form.replace("pouká", "po@uká")
    word_form = word_form.replace("poukl", "po@ukl")
    word_form = word_form.replace("poulič", "po@ulič")
    word_form = word_form.replace("poum", "po@um")
    word_form = word_form.replace("poupr", "po@upr")
    word_form = word_form.replace("pouráž", "po@uráž")
    word_form = word_form.replace("pousm", "po@usm")
    word_form = word_form.replace("poust", "po@ust")
    word_form = word_form.replace("poute", "po@ute")
    word_form = word_form.replace("pouvaž", "po@uvaž")
    word_form = word_form.replace("pouzen", "po@uzen")
    word_form = word_form.replace("douč", "do@uč")
    word_form = word_form.replace("douprav", "do@uprav")
    word_form = word_form.replace("doužív", "do@užív")
    word_form = word_form.replace("douzov", "do@uzov")
    word_form = word_form.replace("doupřesn", "do@upřesn")
    word_form = word_form.replace("doudit", "do@udit")
    word_form = word_form.replace("doudí", "do@udí")
    word_form = word_form.replace("eufemism", "Efemism")
    word_form = word_form.replace("eufor", "Efor")
    word_form = word_form.replace("euro", "Ero")
    word_form = word_form.replace("eutan", "Etan")
    word_form = word_form.replace("farmaceut", "farmacEt")
    word_form = word_form.replace("feud", "fEd")
    word_form = word_form.replace("koloseu", "KolosE")
    word_form = word_form.replace("koreu", "korE")
    word_form = word_form.replace("leuk", "lEk")
    word_form = word_form.replace("linoleu", "linolE")
    word_form = word_form.replace("mauzoleu", "mauzolE")
    word_form = word_form.replace("muzeu", "muzE")
    word_form = word_form.replace("neutral", "nEtral")
    word_form = word_form.replace("neutrál", "nEtrál")
    word_form = word_form.replace("pneum", "pnEm")
    word_form = word_form.replace("pseudo", "psEdo")
    word_form = word_form.replace("terapeut", "terapEt")
    word_form = word_form.replace("eufon", "Efon")
    word_form = word_form.replace("eunuch", "Enuch")
    word_form = word_form.replace("eunuš", "Enuš")
    word_form = word_form.replace("zeugm", "zEgm")
    word_form = word_form.replace("jubileu", "jubilE")
    word_form = word_form.replace("eucken", "Ecken")
    word_form = word_form.replace("kreuzmann", "krEzmann")
    word_form = word_form.replace("pilocereus", "pilocerEs")
    word_form = word_form.replace("cephalocereus", "cephalocerEs")
    word_form = word_form.replace("ie", "ije")
    word_form = word_form.replace("dě", "ďe")
    word_form = word_form.replace("tě", "ťe")
    word_form = word_form.replace("ně", "ňe")
    word_form = word_form.replace("mě", "MNĚ")
    word_form = word_form.replace("ě", "je")
    word_form = word_form.replace("x", "KS")
    word_form = word_form.replace("ch", "X")
    word_form = word_form.replace("q", "KW")
    word_form = word_form.replace("ou", "O")
    word_form = word_form.replace("au", "A")
    word_form = word_form.replace("@", "")

    return word_form


def create_treebank(filename):
    """combines all the functions and returns a complete treebank data structure"""

    a_treebank = load_treebank(filename)

    return a_treebank

