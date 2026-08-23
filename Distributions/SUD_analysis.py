import os
import csv
from subprocess import run
import pandas as pd
from collections import Counter
#from scipy.stats import kendalltau
import shutil

###################### distribuce #####################
def extract_deprel(unit_node):
    """
    Helper function to form a unit's deprel from its constituent words.
    Adjust '.word_list' if your word array is named differently (e.g., '.words').
    """
    # Extracts the deprel from each word and joins them with an underscore
    return "_".join([word.deprel for word in unit_node.word_list])


def get_deprel_distribuce(a_treebank, path, name, k, unit):
    """creates a distribution of LDS deprel instead of word forms"""

    # We will collect the extracted deprels here
    collected_deprels = []

    for sentence in a_treebank.sentence_list:
        # Check your specific filtering conditions
        valid_sentence = False
        if ((k == 'jen_filtr' and sentence.root_good and not sentence.bad_things)
                or (k == 'bez_conj' and sentence.root_good and not sentence.bad_things and sentence.num_conj == 0)
                or (k == 'bez_conj1' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 1)
                or (k == 'bez_conj2' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 2)
                or (k == 'bez_conj3' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 3)):
            valid_sentence = True

        if valid_sentence:
            if unit == "sentence":
                collected_deprels.append(extract_deprel(sentence))

            elif unit == "main_clause":
                for main_clause in sentence.main_clause_list:
                    collected_deprels.append(extract_deprel(main_clause))

            elif unit == "clause":
                for main_clause in sentence.main_clause_list:
                    for clause in main_clause.clause_list:
                        collected_deprels.append(extract_deprel(clause))

            elif unit == "phrase":
                for main_clause in sentence.main_clause_list:
                    for clause in main_clause.clause_list:
                        for phrase in clause.phrase_list:
                            collected_deprels.append(extract_deprel(phrase))

            elif unit == "big_chunk":
                for main_clause in sentence.main_clause_list:
                    for clause in main_clause.clause_list:
                        for phrase in clause.phrase_list:
                            for big_chunk in phrase.big_chunk_list:
                                collected_deprels.append(extract_deprel(big_chunk))

            elif unit == "chunk":
                for main_clause in sentence.main_clause_list:
                    for clause in main_clause.clause_list:
                        for phrase in clause.phrase_list:
                            for big_chunk in phrase.big_chunk_list:
                                for chunk in big_chunk.chunk_list:
                                    collected_deprels.append(extract_deprel(chunk))

    # Calculate frequencies using a dictionary
    deprel_dict = {}
    for deprel_str in collected_deprels:
        if deprel_str in deprel_dict:
            deprel_dict[deprel_str] += 1
        else:
            deprel_dict[deprel_str] = 1

    # Sort the dictionary by frequency (descending)
    sorted_deprel_dict = dict(sorted(deprel_dict.items(), key=lambda x: x[1], reverse=True))

    # Setup the directory path for deprel outputs
    path_deprel = path + '/deprel/'
    if not os.path.exists(path_deprel):
        os.makedirs(path_deprel)

    # Generate the output file
    file_name = f"{path_deprel}{name}_{unit}_deprel.csv"
    with open(file_name, mode='w', encoding='utf-8') as output:
        print('deprel' + ';' + 'frequency', file=output)
        for key, value in sorted_deprel_dict.items():
            print(str(key) + ';' + str(value), file=output)

def get_distribuce (a_treebank, path, name, k, unit):
    """creates a distribution of LDS word forms, LDS syn. function and LDS length"""

    if unit == "sentence":
        sentence_word_form = []
        for sentence in a_treebank.sentence_list:
            if ((k == 'jen_filtr' and sentence.root_good and not sentence.bad_things)
                    or (k == 'bez_conj' and sentence.root_good and not sentence.bad_things and sentence.num_conj == 0)
                    or (k == 'bez_conj1' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 1)
                    or (k == 'bez_conj2' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 2)
                    or (k == 'bez_conj3' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 3)):
                sentence_word_form.append(sentence.word_form)

        sentence_word_dict = {}
        for sentence in sentence_word_form:
            if sentence in sentence_word_dict:
                sentence_word_dict[sentence] += 1
            else:
                sentence_word_dict[sentence] = 1

        sentence_word_dict = (dict(sorted(sentence_word_dict.items(), key=lambda x: x[1], reverse=True)))

        path_word_form = path + '/word_form/'
        if not os.path.exists(path_word_form):
            os.makedirs(path_word_form)

        with open(path_word_form + name + '_sentence_word_form.csv', mode='w', encoding='utf-8') as output:
            print('word_form' + ';' + 'frequency', file=output)
            for key, value in sentence_word_dict.items():
                print(str(key) + ';' + str(value), file=output)

    if unit == "main_clause":
        main_clause_word_form = []

        for sentence in a_treebank.sentence_list:
            if ((k == 'jen_filtr' and sentence.root_good and not sentence.bad_things)
                    or (k == 'bez_conj' and sentence.root_good and not sentence.bad_things and sentence.num_conj == 0)
                    or (k == 'bez_conj1' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 1)
                    or (k == 'bez_conj2' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 2)
                    or (k == 'bez_conj3' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 3)):
                for main_clause in sentence.main_clause_list:
                    main_clause_word_form.append(main_clause.word_form)

        main_clause_word_dict = {}
        for main_clause in main_clause_word_form:
            if main_clause in main_clause_word_dict:
                main_clause_word_dict[main_clause] += 1
            else:
                main_clause_word_dict[main_clause] = 1

        main_clause_word_dict = (dict(sorted(main_clause_word_dict.items(), key=lambda x: x[1], reverse=True)))

        path_word_form = path + '/word_form/'
        if not os.path.exists(path_word_form):
            os.makedirs(path_word_form)


        with open(path_word_form + name + '_main_clause_word_form.csv', mode='w', encoding='utf-8') as output:
            print('word_form' + ';' + 'frequency', file=output)
            for key, value in main_clause_word_dict.items():
                print(str(key) + ';' + str(value), file=output)


    if unit == "clause":
        clause_word_form = []

        for sentence in a_treebank.sentence_list:
            if ((k == 'jen_filtr' and sentence.root_good and not sentence.bad_things)
                    or (k == 'bez_conj' and sentence.root_good and not sentence.bad_things and sentence.num_conj == 0)
                    or (k == 'bez_conj1' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 1)
                    or (k == 'bez_conj2' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 2)
                    or (k == 'bez_conj3' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 3)):
                for main_clause in sentence.main_clause_list:
                    for clause in main_clause.clause_list:
                        clause_word_form.append(clause.word_form)

        clause_word_dict = {}
        for clause in clause_word_form:
            if clause in clause_word_dict:
                clause_word_dict[clause] += 1
            else:
                clause_word_dict[clause] = 1

        clause_word_dict = (dict(sorted(clause_word_dict.items(), key=lambda x: x[1], reverse=True)))

        path_word_form = path + '/word_form/'
        if not os.path.exists(path_word_form):
            os.makedirs(path_word_form)


        with open(path_word_form + name + '_clause_word_form.csv', mode='w', encoding='utf-8') as output:
            print('word_form' + ';' + 'frequency', file=output)
            for key, value in clause_word_dict.items():
                print(str(key) + ';' + str(value), file=output)

    if unit == "phrase":
        phrase_word_form = []

        for sentence in a_treebank.sentence_list:
            if ((k == 'jen_filtr' and sentence.root_good and not sentence.bad_things)
                    or (k == 'bez_conj' and sentence.root_good and not sentence.bad_things and sentence.num_conj == 0)
                    or (k == 'bez_conj1' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 1)
                    or (k == 'bez_conj2' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 2)
                    or (k == 'bez_conj3' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 3)):
                for main_clause in sentence.main_clause_list:
                    for clause in main_clause.clause_list:
                        for phrase in clause.phrase_list:
                            phrase_word_form.append(phrase.word_form)

        phrase_word_dict = {}
        for phrase in phrase_word_form:
            if phrase in phrase_word_dict:
                phrase_word_dict[phrase] += 1
            else:
                phrase_word_dict[phrase] = 1

        phrase_word_dict = (dict(sorted(phrase_word_dict.items(), key=lambda x: x[1], reverse=True)))

        path_word_form = path + '/word_form/'
        if not os.path.exists(path_word_form):
            os.makedirs(path_word_form)


        with open(path_word_form + name + '_phrase_word_form.csv', mode='w', encoding='utf-8') as output:
            print('word_form' + ';' + 'frequency', file=output)
            for key, value in phrase_word_dict.items():
                print(str(key) + ';' + str(value), file=output)

    if unit == "big_chunk":
        big_chunk_word_form = []

        for sentence in a_treebank.sentence_list:
            if ((k == 'jen_filtr' and sentence.root_good and not sentence.bad_things)
                    or (k == 'bez_conj' and sentence.root_good and not sentence.bad_things and sentence.num_conj == 0)
                    or (k == 'bez_conj1' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 1)
                    or (k == 'bez_conj2' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 2)
                    or (k == 'bez_conj3' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 3)):
                for main_clause in sentence.main_clause_list:
                    for clause in main_clause.clause_list:
                        for phrase in clause.phrase_list:
                            for big_chunk in phrase.big_chunk_list:
                                big_chunk_word_form.append(big_chunk.word_form)

        big_chunk_word_dict = {}
        for big_chunk in big_chunk_word_form:
            if big_chunk in big_chunk_word_dict:
                big_chunk_word_dict[big_chunk] += 1
            else:
                big_chunk_word_dict[big_chunk] = 1

        big_chunk_word_dict = (dict(sorted(big_chunk_word_dict.items(), key=lambda x: x[1], reverse=True)))

        path_word_form = path + '/word_form/'
        if not os.path.exists(path_word_form):
            os.makedirs(path_word_form)


        with open(path_word_form + name + '_big_chunk_word_form.csv', mode='w', encoding='utf-8') as output:
            print('word_form' + ';' + 'frequency', file=output)
            for key, value in big_chunk_word_dict.items():
                print(str(key) + ';' + str(value), file=output)

    if unit == "chunk":
        chunk_word_form = []

        for sentence in a_treebank.sentence_list:
            if ((k == 'jen_filtr' and sentence.root_good and not sentence.bad_things)
                    or (k == 'bez_conj' and sentence.root_good and not sentence.bad_things and sentence.num_conj == 0)
                    or (k == 'bez_conj1' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 1)
                    or (k == 'bez_conj2' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 2)
                    or (k == 'bez_conj3' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 3)):
                for main_clause in sentence.main_clause_list:
                    for clause in main_clause.clause_list:
                        for phrase in clause.phrase_list:
                            for big_chunk in phrase.big_chunk_list:
                                for chunk in big_chunk.chunk_list:
                                    chunk_word_form.append(chunk.word_form)

        chunk_word_dict = {}
        for chunk in chunk_word_form:
            if chunk in chunk_word_dict:
                chunk_word_dict[chunk] += 1
            else:
                chunk_word_dict[chunk] = 1

        chunk_word_dict = (dict(sorted(chunk_word_dict.items(), key=lambda x: x[1], reverse=True)))

        path_word_form = path + '/word_form/'
        if not os.path.exists(path_word_form):
            os.makedirs(path_word_form)

        with open(path_word_form + name + '_chunk_word_form.csv', mode='w', encoding='utf-8') as output:
            print('word_form' + ';' + 'frequency', file=output)
            for key, value in chunk_word_dict.items():
                print(str(key) + ';' + str(value), file=output)

def get_frequency_distribuce(a_treebank, path, name, k, unit):
    """Creates a distribution of how many distinct word forms share the exact same frequency."""

    if unit == "phrase":
        phrase_word_form = []

        for sentence in a_treebank.sentence_list:
            if ((k == 'jen_filtr' and sentence.root_good and not sentence.bad_things)
                    or (k == 'bez_conj' and sentence.root_good and not sentence.bad_things and sentence.num_conj == 0)
                    or (k == 'bez_conj1' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 1)
                    or (k == 'bez_conj2' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 2)
                    or (k == 'bez_conj3' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 3)):
                for main_clause in sentence.main_clause_list:
                    for clause in main_clause.clause_list:
                        for phrase in clause.phrase_list:
                            phrase_word_form.append(phrase.word_form)

        # 1. Get word frequencies
        phrase_word_dict = {}
        for phrase in phrase_word_form:
            if phrase in phrase_word_dict:
                phrase_word_dict[phrase] += 1
            else:
                phrase_word_dict[phrase] = 1

        phrase_word_dict = (dict(sorted(phrase_word_dict.items(), key=lambda x: x[1], reverse=True)))


        # 2. Get frequency of frequencies
        freq_of_freq_dict = {}
        for word, freq in phrase_word_dict.items():
            if freq in freq_of_freq_dict:
                freq_of_freq_dict[freq] += 1
            else:
                freq_of_freq_dict[freq] = 1

        freq_of_freq_dict = dict(sorted(freq_of_freq_dict.items(), key=lambda x: x[0], reverse=True))

        path_freq_dist = path + '/frequency_distribution/'
        if not os.path.exists(path_freq_dist):
            os.makedirs(path_freq_dist)

        with open(path_freq_dist + name + '_phrase_freq_dist.csv', mode='w', encoding='utf-8') as output:
            print('frequency;number_of_word_forms', file=output)
            for freq, count in freq_of_freq_dict.items():
                print(str(freq) + ';' + str(count), file=output)


    if unit == "big_chunk":
        big_chunk_word_form = []

        for sentence in a_treebank.sentence_list:
            if ((k == 'jen_filtr' and sentence.root_good and not sentence.bad_things)
                    or (k == 'bez_conj' and sentence.root_good and not sentence.bad_things and sentence.num_conj == 0)
                    or (k == 'bez_conj1' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 1)
                    or (k == 'bez_conj2' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 2)
                    or (k == 'bez_conj3' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 3)):
                for main_clause in sentence.main_clause_list:
                    for clause in main_clause.clause_list:
                        for phrase in clause.phrase_list:
                            for big_chunk in phrase.big_chunk_list:
                                big_chunk_word_form.append(big_chunk.word_form)

        # 1. Get word frequencies
        big_chunk_word_dict = {}
        for big_chunk in big_chunk_word_form:
            if big_chunk in big_chunk_word_dict:
                big_chunk_word_dict[big_chunk] += 1
            else:
                big_chunk_word_dict[big_chunk] = 1

        # 2. Get frequency of frequencies
        freq_of_freq_dict = {}
        for word, freq in big_chunk_word_dict.items():
            if freq in freq_of_freq_dict:
                freq_of_freq_dict[freq] += 1
            else:
                freq_of_freq_dict[freq] = 1

        freq_of_freq_dict = dict(sorted(freq_of_freq_dict.items(), key=lambda x: x[0], reverse=True))

        path_freq_dist = path + '/frequency_distribution/'
        if not os.path.exists(path_freq_dist):
            os.makedirs(path_freq_dist)

        with open(path_freq_dist + name + '_big_chunk_freq_dist.csv', mode='w', encoding='utf-8') as output:
            print('frequency;number_of_word_forms', file=output)
            for freq, count in freq_of_freq_dict.items():
                print(str(freq) + ';' + str(count), file=output)


    if unit == "chunk":
        chunk_word_form = []

        for sentence in a_treebank.sentence_list:
            if ((k == 'jen_filtr' and sentence.root_good and not sentence.bad_things)
                    or (k == 'bez_conj' and sentence.root_good and not sentence.bad_things and sentence.num_conj == 0)
                    or (k == 'bez_conj1' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 1)
                    or (k == 'bez_conj2' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 2)
                    or (k == 'bez_conj3' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 3)):
                for main_clause in sentence.main_clause_list:
                    for clause in main_clause.clause_list:
                        for phrase in clause.phrase_list:
                            for big_chunk in phrase.big_chunk_list:
                                for chunk in big_chunk.chunk_list:
                                    chunk_word_form.append(chunk.word_form)

        # 1. Get word frequencies
        chunk_word_dict = {}
        for chunk in chunk_word_form:
            if chunk in chunk_word_dict:
                chunk_word_dict[chunk] += 1
            else:
                chunk_word_dict[chunk] = 1

        # 2. Get frequency of frequencies
        freq_of_freq_dict = {}
        for word, freq in chunk_word_dict.items():
            if freq in freq_of_freq_dict:
                freq_of_freq_dict[freq] += 1
            else:
                freq_of_freq_dict[freq] = 1

        freq_of_freq_dict = dict(sorted(freq_of_freq_dict.items(), key=lambda x: x[0], reverse=True))

        path_freq_dist = path + '/frequency_distribution/'
        if not os.path.exists(path_freq_dist):
            os.makedirs(path_freq_dist)

        with open(path_freq_dist + name + '_chunk_freq_dist.csv', mode='w', encoding='utf-8') as output:
            print('frequency;number_of_word_forms', file=output)
            for freq, count in freq_of_freq_dict.items():
                print(str(freq) + ';' + str(count), file=output)

def save_length_distribution(unit_name, length_data, base_path, name):
    path = os.path.join(base_path, f'length')
    os.makedirs(path, exist_ok=True)

    length_dict = dict(sorted(Counter(length_data).items()))
    file_path = os.path.join(path, f'{name}_{unit_name}_length.csv')

    with open(file_path, mode='w', encoding='utf-8') as output:
        print('length;frequency', file=output)
        for length, frequency in length_dict.items():
            print(f'{length};{frequency}', file=output)

def process_units(a_treebank, path, name, k, unit):
    length_by_unit = {
        "main_clause": [],
        "clause": [],
        "phrase": [],
        "big_chunk": [],
        "chunk": [],
        "word":[]
    }
    for sentence in a_treebank.sentence_list:
        if ((k == 'jen_filtr' and sentence.root_good and not sentence.bad_things)
                or (k == 'bez_conj' and sentence.root_good and not sentence.bad_things and sentence.num_conj == 0)
                or (k == 'bez_conj1' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 1)
                or (k == 'bez_conj2' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 2)
                or (k == 'bez_conj3' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 3)):

            if unit == "sentence":
                length_by_unit["main_clause"].append(sentence.length_by_main_clause)
                length_by_unit["clause"].append(sentence.length_by_clause)
                length_by_unit["phrase"].append(sentence.length_by_phrase)
                length_by_unit["big_chunk"].append(sentence.length_by_big_chunk)
                length_by_unit["chunk"].append(sentence.length_by_chunk)
                length_by_unit["word"].append(len(sentence.word_list_no_punct))

            for mainclause in sentence.main_clause_list:
                if unit == "main_clause":
                    length_by_unit["clause"].append(mainclause.length_by_clause)
                    length_by_unit["phrase"].append(mainclause.length_by_phrase)
                    length_by_unit["big_chunk"].append(mainclause.length_by_big_chunk)
                    length_by_unit["chunk"].append(mainclause.length_by_chunk)
                    length_by_unit["word"].append(len(mainclause.word_list))

                for clause in mainclause.clause_list:
                    if unit == "clause":
                        length_by_unit["phrase"].append(clause.length_by_phrase)
                        length_by_unit["big_chunk"].append(clause.length_by_big_chunk)
                        length_by_unit["chunk"].append(clause.length_by_chunk)
                        length_by_unit["word"].append(len(clause.word_list))

                    for phrase in clause.phrase_list:
                        if unit == "phrase":
                            length_by_unit["big_chunk"].append(phrase.length_by_big_chunk)
                            length_by_unit["chunk"].append(phrase.length_by_chunk)
                            length_by_unit["word"].append(len(phrase.word_list))

                        for bigchunk in phrase.big_chunk_list:
                            if unit == "big_chunk":
                                length_by_unit["chunk"].append(bigchunk.length_by_chunk)
                                length_by_unit["word"].append(len(bigchunk.word_list))

                            for chunk in bigchunk.chunk_list:
                                if unit == "chunk":
                                    length_by_unit["word"].append(len(chunk.word_list))

    for subunit, lengths in length_by_unit.items():
        #print(f"Unit: {unit}, Subunit: {subunit}, Lengths: {lengths}")
        if lengths:
            save_length_distribution(subunit, lengths, path, name)

def extract_frequencies(input_file):
    """Extracts frequencies from the second column of the input CSV file."""

    frequencies = []

    with open(input_file, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter=';')
        next(reader)  # Skip the header row

        for row in reader:
            if len(row) >= 2:  # Check if row has at least 2 columns
                frequencies.append(row[1])

    return frequencies


def create_frequency_file(output_file, frequencies):
    """Creates a new CSV file with frequencies and ranks."""

    ranks = range(1, len(frequencies) + 1)

    with open(output_file, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Rank', 'Frequency'])

        for rank, frequency in zip(ranks, frequencies):
            writer.writerow([rank, frequency])


def prepare_program_file_dis(input_file, program_file):
    """Creates a program file for NLREG with the specified function."""

    frequencies = extract_frequencies(input_file)
    '''
    if len(frequencies) != 0:
        #constant = 'Constant firstConstr = ' + frequencies[0] + ';'
        variables = 'Variables x, y;'
        parameter = 'Parameter a; Parameter b;'
        function = 'Function y = a * (x^(-b)) + 1;'
        data = 'Data;'
        '''

    if len(frequencies) != 0:
        constant = 'Constant f1 = ' + frequencies[0] + ';'
        variables = 'Variables x, y;'
        #parameter = 'Parameters a;'
        #function = 'Function y = f1 * (x^(-a));'
        parameter = 'Parameters a, b;'
        function = 'Function y = f1 * ((x + b) / (1 + b))^(-a);'
        data = 'Data;'

        with open(program_file, mode='w', encoding='utf-8') as output:
            print(variables, file=output)
            print(constant, file=output)
            print(parameter, file=output)
            print(function, file=output)
            print(data, file=output)

            for index, frequency in enumerate(frequencies, start=1):
                print(index, frequency, file=output)


def run_nlreg_dis(input_file, output_folder):
    """Runs NLREG using the specified input file and output folder."""

    input_file_split = os.path.splitext(os.path.basename(input_file))
    program_file = os.path.join(output_folder, input_file_split[0] + ".prg")
    output_file = os.path.join(output_folder, input_file_split[0] + '_nlreg.lst')

    prepare_program_file_dis(input_file, program_file)

    run(['C:/Users/nogol/Documents/Doktorat/NLREG/NLREGCA.exe', program_file, '/list', output_file])


def process_csv_files(input_folder, output_folder):
    """Processes all CSV files in the specified input folder and saves output in the specified output folder."""
    """.csv oděleno středníkem, header included"""

    files = os.listdir(input_folder)
    csv_files = [file for file in files if file.endswith('.csv')]

    for csv_file in csv_files:
        input_file = os.path.join(input_folder, csv_file)
        run_nlreg_dis(input_file, output_folder)


def process_lst_files_dis(output_folder, output_csv=None):
    """Processes NLREG output files (.lst) in the specified output folder and optionally saves the result as a CSV file."""

    file_data = []

    for filename in os.listdir(output_folder):
        if filename.endswith(".lst"):
            file_path = os.path.join(output_folder, filename)
            data = extract_info_from_lst_dis(file_path)
            data['Parameter a'] = get_first_constr_dis(file_path)
            file_data.append(data)

    df = pd.DataFrame(file_data, columns=['File Name', 'R^2', 'Parameter a', 'Parameter b'])

    if output_csv:
        output_path = os.path.join(output_csv, '01NLREG_distribuce.csv')
        df.to_csv(output_path, index=False)

    return df


def extract_info_from_lst_dis(lst_file):
    """Extracts information from a single NLREG output file (.lst)."""

    with open(lst_file, 'r') as file:
        lines = file.readlines()

    '''
    r_squared_line = [line for line in lines if line.startswith('Proportion of variance explained (R^2)')]
    parameter_b_line = [line for line in lines if line.startswith('         b')]
    parameter_a_line = [line for line in lines if line.startswith('         a')]

    if r_squared_line and parameter_b_line and parameter_a_line:
        r_squared = r_squared_line[0].split('=')[1].split('(')[0].strip()
        parameter_b = parameter_b_line[0].split()[2]
        parameter_a = parameter_a_line[0].split()[2]
        return {'File Name': os.path.basename(lst_file), 'R^2': r_squared, 'Parameter a': parameter_a, 'Parameter b': parameter_b}

    return {'File Name': os.path.basename(lst_file), 'R^2': None, 'Parameter a': None, 'Parameter b': None}
    '''
    r_squared_line = [line for line in lines if line.startswith('Proportion of variance explained (R^2)')]
    parameter_b_line = [line for line in lines if line.startswith('         b')]

    if r_squared_line and parameter_b_line:
        r_squared = r_squared_line[0].split('=')[1].split('(')[0].strip()
        parameter_b = parameter_b_line[0].split()[2]
        return {'File Name': os.path.basename(lst_file), 'R^2': r_squared, 'Parameter b': parameter_b}

    return {'File Name': os.path.basename(lst_file), 'R^2': None, 'Parameter b': None}

def get_first_constr_dis(lst_file):
    """Extracts the value of firstConstr from a single NLREG output file (.lst)."""
    # Implement the code to extract the firstConstr value from the .lst file
    # and return it as a string or None if not found.

    with open(lst_file, 'r') as file:
        lines = file.readlines()

    for line in lines:
        if line.startswith('   2: Constant firstConstr = '):
            first_constr = line.split('=')[1].strip().rstrip(';')
            return first_constr

    return None


def load_and_sort_csv_files(input_folder, output_folder):
    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Get a list of CSV files in the input folder
    csv_files = [f for f in os.listdir(input_folder) if f.endswith('.csv')]

    # Process each CSV file
    for file_name in csv_files:
        # Read the CSV file into a pandas DataFrame
        file_path = os.path.join(input_folder, file_name)
        df = pd.read_csv(file_path, sep=';')
        #print(df)

        # Sort the DataFrame based on the 'lds' column
        df_sorted = df.sort_values('length')
        #print(df_sorted)

        # Create the output file path
        file_name_no_ext = os.path.splitext(file_name)[0]
        output_file_path = os.path.join(output_folder, file_name_no_ext + '.txt')

        # Extract only the 'lds' and 'frce' columns
        df_extracted = df_sorted[['length', 'frequency']]

        # Save the extracted data as a tab-separated .txt file without the header row
        df_extracted.to_csv(output_file_path, sep='\t', index=False, header=False)