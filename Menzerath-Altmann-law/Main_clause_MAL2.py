import os
import csv
from subprocess import run
import pandas as pd
import shutil


def calculate_xfy(input_file, output_file, construct_column, constituent_column):
    """calculates construct lengths, their frequencies and constituent lengths"""

    input_df = pd.read_csv(input_file, delimiter='\t', quoting=csv.QUOTE_NONE, low_memory=False)
    construct_dict = {}

    # filters out records where constituent lengths equal zero
    #index_to_be_drop = input_df[input_df[constituent_column] == 0].index
    #input_df.drop(index_to_be_drop, inplace=True)

    unique_constructs = input_df[construct_column].unique()
    construct_n = input_df.groupby(construct_column)[constituent_column].count()
    constituent_sum = input_df.groupby(construct_column)[constituent_column].sum()

    # filters out records where construct lengths equal zero
    for value in unique_constructs:
        #if value != 0:
            #construct_dict[value] = {}
        construct_dict[value] = {}

    for value in construct_dict:
        if value != 0:
            construct_dict[value]['frequency'] = construct_n[value]
            construct_dict[value]['avg_constituent_len'] = constituent_sum[value]/construct_n[value]/value
        else:
            construct_dict[value]['frequency'] = construct_n[value]
            construct_dict[value]['avg_constituent_len'] = constituent_sum[value]/construct_n[value]

    xfy_df = pd.DataFrame.from_dict(construct_dict, orient="index").sort_index()
    xfy_df.to_csv(path_or_buf=output_file, sep='\t', index_label=['construct'])


def calculate_values(xfy_list, index_1, index_2):
    """calculates required values .. too tired to write a comment here"""

    total_frequency = xfy_list[index_1]['frequency'] + xfy_list[index_2]['frequency']
    w_avg_construct_1 = xfy_list[index_1]['construct'] * xfy_list[index_1]['frequency']
    w_avg_construct_2 = xfy_list[index_2]['construct'] * xfy_list[index_2]['frequency']
    w_avg_construct = (w_avg_construct_1 + w_avg_construct_2) / total_frequency
    w_avg_constituent_1 = xfy_list[index_1]['avg_constituent_len'] * xfy_list[index_1]['frequency']
    w_avg_constituent_2 = xfy_list[index_2]['avg_constituent_len'] * xfy_list[index_2]['frequency']
    w_avg_constituent = (w_avg_constituent_1 + w_avg_constituent_2) / total_frequency

    return w_avg_construct, total_frequency, w_avg_constituent


def calculate_weighted_xfy(input_file, output_file, constant):
    """loads xfy data and calculates weighted average (if applicable), bottom-up"""

    xfy_df = pd.read_csv(input_file, delimiter='\t', quoting=csv.QUOTE_NONE)
    xfy_list = xfy_df.to_dict('records')

    for index in range(len(xfy_list) - 1, -1, -1):
        if index > 0 and xfy_list[index]['frequency'] < constant:
            x, f, y = calculate_values(xfy_list, index, index - 1)
            xfy_list[index - 1]['construct'] = x
            xfy_list[index - 1]['frequency'] = f
            xfy_list[index - 1]['avg_constituent_len'] = y
            xfy_list.pop(index)

        elif index == 0 and xfy_list[index]['frequency'] < constant and xfy_list[index]['construct'] == 1:
            x, f, y = calculate_values(xfy_list, index, index + 1)
            xfy_list[index + 1]['construct'] = x
            xfy_list[index + 1]['frequency'] = f
            xfy_list[index + 1]['avg_constituent_len'] = y
            xfy_list.pop(index)

        elif index == 0 and xfy_list[index]['construct'] == 0:
            x, f, y = calculate_values(xfy_list, index, index + 1)
            xfy_list[index + 1]['construct'] = x
            xfy_list[index + 1]['frequency'] = f
            xfy_list[index + 1]['avg_constituent_len'] = y
            xfy_list.pop(index)

    with open(output_file, mode='w', encoding='utf-8') as output:
        print('construct' + '\t' + 'frequency' + '\t' + 'avg_constituent_len', file=output)  # header

        for xfy_dict in xfy_list:
            print(str(xfy_dict['construct']) + '\t' + str(xfy_dict['frequency']) + '\t' + str(xfy_dict['avg_constituent_len']), file=output)


def process_types(input_file, output_file, column_name):
    """loads quantified data of word tokens, drops duplicates, saves quantified data for phrase types"""

    token_df = pd.read_csv(input_file, delimiter='\t', quoting=csv.QUOTE_NONE, dtype={0: 'str'})
    type_df = token_df.drop_duplicates(subset=[column_name])
    type_df.to_csv(path_or_buf=output_file, sep='\t', index=False)


def get_weight_avg_limit(a_treebank, k):

    type_sentences = []
    type_main_clauses = []
    type_clauses = []
    type_phrases = []
    type_big_chunk = []
    type_chunk_big_chunk = []
    type_chunk_big_chunk2 = []
    type_word = []

    for sentence in a_treebank.sentence_list:
        podminka = k == 'bez_conj_a_cond' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj == 0
        podminka2 = k == 'bez_cond' and sentence.root_good and not sentence.bad_things and not sentence.condicional
        podminka3 = k == 'jen_filtr' and sentence.root_good and not sentence.bad_things
        podminka4 = k == 'bez_cond_conj1' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj <= 1
        podminka5 = k == 'bez_conj' and sentence.root_good and not sentence.bad_things and sentence.num_conj == 0
        podminka6 = k == 'bez_conj1' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 1
        podminka7 = k == 'bez_cond_conj2' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj <= 2
        podminka8 = k == 'bez_conj2' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 2
        podminka9 = k == 'bez_cond_conj3' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj <= 3
        podminka10 = k == 'bez_conj3' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 3
        if podminka or podminka2 or podminka3 or podminka4 or podminka5 or podminka6 or podminka7 or podminka8 or podminka9 or podminka10:
            type_sentences.append(sentence.word_form)
            for main_clause in sentence.main_clause_list:
                type_main_clauses.append(main_clause.word_form)
                for clause in main_clause.clause_list:
                    type_clauses.append(clause.word_form)
                    for phrase in clause.phrase_list:
                        type_phrases.append(phrase.word_form)
                        for big_chunk in phrase.big_chunk_list:
                            type_big_chunk.append(big_chunk.word_form)
                            for chunk in big_chunk.chunk_list:
                                type_chunk_big_chunk.append(chunk.word_form)
                            for chunk2 in big_chunk.chunk2_list:
                                type_chunk_big_chunk2.append(chunk2.word_form)
            for word in sentence.word_list:
                type_word.append(word.form)

    type_sentences = set(type_sentences)
    type_main_clauses = set(type_main_clauses)
    type_clauses = set(type_clauses)
    type_phrases = set(type_phrases)
    type_big_chunk = set(type_big_chunk)
    type_chunk_big_chunk = set(type_chunk_big_chunk)
    type_chunk_big_chunk2 = set(type_chunk_big_chunk2)
    type_word = set(type_word)
    n_type_sentences = len(type_sentences)
    n_type_main_clauses = len(type_main_clauses)
    n_type_clause = len(type_clauses)
    n_type_phrases = len(type_phrases)
    n_type_big_chunk = len(type_big_chunk)
    n_type_chunk_big_chunk = len(type_chunk_big_chunk)
    n_type_chunk_big_chunk2 = len(type_chunk_big_chunk2)
    n_type_word = len(type_word)
    weight_a_sent = n_type_sentences / 1000
    weight_a_main_clause = n_type_main_clauses / 1000
    weight_a_clause = n_type_clause / 1000
    weight_a_phrase = n_type_phrases / 1000
    weight_a_big_chunk = n_type_big_chunk / 1000
    weight_a_chunk_big_chunk = n_type_chunk_big_chunk / 1000
    weight_a_chunk_big_chunk2 = n_type_chunk_big_chunk2 / 1000
    weight_a_word = n_type_word / 1000

    return weight_a_sent, weight_a_main_clause, weight_a_clause, weight_a_phrase, weight_a_big_chunk, weight_a_chunk_big_chunk, weight_a_chunk_big_chunk2, weight_a_word

def sentence_mainclause_clause_cut(a_treebank, weighted_avg_limit_sentence, file_path_s, k):

    print('sentence_mainclause_clause_cut')
    mainclause_n = 0  # number of main clauses
    clause_n = 0  # number of clauses

    #tokens
    with open(file_path_s + 'sen_maincl_cl_cut.txt', mode='w', encoding='utf-8') as output:
        print('sent_id' + '\t' + 'sent_text' + '\t' + 'mainclause_n' + '\t' + 'predicates_main'+ '\t' + 'mainclause_text' + '\t' + 'clause_n' + '\t' + 'clause_text', file=output)  # header

        for sentence in a_treebank.sentence_list:
            podminka = k == 'bez_conj_a_cond' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj == 0
            podminka2 = k == 'bez_cond' and sentence.root_good and not sentence.bad_things and not sentence.condicional
            podminka3 = k == 'jen_filtr' and sentence.root_good and not sentence.bad_things
            podminka4 = k == 'bez_cond_conj1' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj <= 1
            podminka5 = k == 'bez_conj' and sentence.root_good and not sentence.bad_things and sentence.num_conj == 0
            podminka6 = k == 'bez_conj1' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 1
            podminka7 = k == 'bez_cond_conj2' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj <= 2
            podminka8 = k == 'bez_conj2' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 2
            podminka9 = k == 'bez_cond_conj3' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj <= 3
            podminka10 = k == 'bez_conj3' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 3
            if podminka or podminka2 or podminka3 or podminka4 or podminka5 or podminka6 or podminka7 or podminka8 or podminka9 or podminka10:
                predicates_main = []
                mainclauses = []
                clauses = []
                for mainclause in sentence.main_clause_list:
                    mainclause_n += 1
                    mainclauses.append(mainclause.word_form)
                    for clause in mainclause.clause_list:
                        clause_n += 1
                        clauses.append(clause.word_form)
                    for word in mainclause.word_list:
                        if word.comment == 'main_clause':
                            predicates_main.append(word.form)

                print(sentence.id + '\t' + sentence.word_form + '\t' + str(mainclause_n) + '\t' + '; '.join(predicates_main)+ '\t' + '; '.join(mainclauses) + '\t' + str(clause_n) + '\t' + '; '.join(clauses), file=output)
                mainclause_n = 0
                clause_n = 0
            else:
                continue

        calculate_xfy(file_path_s + 'sen_maincl_cl_cut.txt', file_path_s + 'sen_maincl_cl_cut_xfy.txt', 'mainclause_n', 'clause_n')
        calculate_weighted_xfy(file_path_s + 'sen_maincl_cl_cut_xfy.txt', file_path_s + 'sen_maincl_cl_cut_xfy_weighted.txt', weighted_avg_limit_sentence)

        # types
        process_types(file_path_s + 'sen_maincl_cl_cut.txt', file_path_s + 'sen_maincl_cl_cut_type.txt', 'sent_text')
        calculate_xfy(file_path_s + 'sen_maincl_cl_cut_type.txt', file_path_s + 'sen_maincl_cl_cut_type_xfy.txt', 'mainclause_n', 'clause_n')
        calculate_weighted_xfy(file_path_s + 'sen_maincl_cl_cut_type_xfy.txt', file_path_s + 'sen_maincl_cl_cut_type_xfy_weighted.txt', weighted_avg_limit_sentence)

def mainclause_clause_phrase_cut(a_treebank, weighted_avg_limit_mainclause, file_path_mc, k):

    print('mainclause_clause_phrase_cut')
    clause_n = 0  # number of lds excluding other clauses
    phrase_n = 0  # number of chunks within LDS

    #tokens
    with open(file_path_mc + 'maincl_cl_phr_cut.txt', mode='w', encoding='utf-8') as output:
        print('sent_id' + '\t' + 'mainclause_text' + '\t' + 'sentence_text' + '\t' + 'clause_n' + '\t' + 'clause_text' + '\t' + 'phrase_n' + '\t' + 'phrase_text', file=output)  # header

        for sentence in a_treebank.sentence_list:
            podminka = k == 'bez_conj_a_cond' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj == 0
            podminka2 = k == 'bez_cond' and sentence.root_good and not sentence.bad_things and not sentence.condicional
            podminka3 = k == 'jen_filtr' and sentence.root_good and not sentence.bad_things
            podminka4 = k == 'bez_cond_conj1' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj <= 1
            podminka5 = k == 'bez_conj' and sentence.root_good and not sentence.bad_things and sentence.num_conj == 0
            podminka6 = k == 'bez_conj1' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 1
            podminka7 = k == 'bez_cond_conj2' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj <= 2
            podminka8 = k == 'bez_conj2' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 2
            podminka9 = k == 'bez_cond_conj3' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj <= 3
            podminka10 = k == 'bez_conj3' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 3
            if podminka or podminka2 or podminka3 or podminka4 or podminka5 or podminka6 or podminka7 or podminka8 or podminka9 or podminka10:
                for mainclause in sentence.main_clause_list:
                    clauses = []
                    phrases = []
                    for clause in mainclause.clause_list:
                        clause_n += 1
                        clauses.append(clause.word_form)
                        for phrase in clause.phrase_list:
                            phrase_n += 1
                            phrases.append(phrase.word_form)
                    print(sentence.id + '\t' + mainclause.word_form + '\t' + sentence.text + '\t' + str(clause_n) + '\t' + ';'.join(clauses) + '\t' + str(phrase_n) + '\t' + ';'.join(phrases), file=output)
                    clause_n = 0
                    phrase_n = 0
            else:
                continue

        calculate_xfy(file_path_mc + 'maincl_cl_phr_cut.txt', file_path_mc + 'maincl_cl_phr_cut_xfy.txt', 'clause_n', 'phrase_n')
        calculate_weighted_xfy(file_path_mc + 'maincl_cl_phr_cut_xfy.txt', file_path_mc + 'maincl_cl_phr_cut_xfy_weighted.txt', weighted_avg_limit_mainclause)

        # types
        process_types(file_path_mc + 'maincl_cl_phr_cut.txt', file_path_mc + 'maincl_cl_phr_cut_type.txt', 'mainclause_text')
        calculate_xfy(file_path_mc + 'maincl_cl_phr_cut_type.txt', file_path_mc + 'maincl_cl_phr_cut_type_xfy.txt', 'clause_n', 'phrase_n')
        calculate_weighted_xfy(file_path_mc + 'maincl_cl_phr_cut_type_xfy.txt', file_path_mc + 'maincl_cl_phr_cut_type_xfy_weighted.txt', weighted_avg_limit_mainclause)

def clause_phrase_big_chunk_cut(a_treebank, weighted_avg_limit_clause, file_path_c, k):

    print('clause_phrase_big_chunk_cut')
    phrase_n = 0  # number of lds excluding other clauses
    big_chunk_n = 0  # number of chunks within LDS

    #tokens
    with open(file_path_c + 'cl_phr_big_chunk_cut.txt', mode='w', encoding='utf-8') as output:
        print('sent_id' + '\t' + 'clause_text' + '\t' + 'sentence_text' + '\t' + 'phrase_n' + '\t' + 'phrase_text' + '\t' + 'big_chunk_n' + '\t' + 'big_chunk_text', file=output)  # header

        for sentence in a_treebank.sentence_list:
            podminka = k == 'bez_conj_a_cond' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj == 0
            podminka2 = k == 'bez_cond' and sentence.root_good and not sentence.bad_things and not sentence.condicional
            podminka3 = k == 'jen_filtr' and sentence.root_good and not sentence.bad_things
            podminka4 = k == 'bez_cond_conj1' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj <= 1
            podminka5 = k == 'bez_conj' and sentence.root_good and not sentence.bad_things and sentence.num_conj == 0
            podminka6 = k == 'bez_conj1' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 1
            podminka7 = k == 'bez_cond_conj2' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj <= 2
            podminka8 = k == 'bez_conj2' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 2
            podminka9 = k == 'bez_cond_conj3' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj <= 3
            podminka10 = k == 'bez_conj3' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 3
            if podminka or podminka2 or podminka3 or podminka4 or podminka5 or podminka6 or podminka7 or podminka8 or podminka9 or podminka10:
                for mainclause in sentence.main_clause_list:
                    for clause in mainclause.clause_list:
                        phrases = []
                        big_chunks = []
                        for phrase in clause.phrase_list:
                            phrase_n += 1
                            phrases.append(phrase.word_form)
                            for big_chunk in phrase.big_chunk_list:
                                big_chunk_n += 1
                                big_chunks.append(big_chunk.word_form)
                        print(sentence.id + '\t' + clause.word_form + '\t' + sentence.text + '\t' + str(phrase_n) + '\t' + ';'.join(phrases) + '\t' + str(big_chunk_n) + '\t' + ';'.join(big_chunks), file=output)
                        phrase_n = 0
                        big_chunk_n = 0
            else:
                continue

        calculate_xfy(file_path_c + 'cl_phr_big_chunk_cut.txt', file_path_c + 'cl_phr_big_chunk_cut_xfy.txt', 'phrase_n', 'big_chunk_n')
        calculate_weighted_xfy(file_path_c + 'cl_phr_big_chunk_cut_xfy.txt', file_path_c + 'cl_phr_big_chunk_cut_xfy_weighted.txt', weighted_avg_limit_clause)

        # types
        process_types(file_path_c + 'cl_phr_big_chunk_cut.txt', file_path_c + 'cl_phr_big_chunk_cut_type.txt', 'clause_text')
        calculate_xfy(file_path_c + 'cl_phr_big_chunk_cut_type.txt', file_path_c + 'cl_phr_big_chunk_cut_type_xfy.txt', 'phrase_n', 'big_chunk_n')
        calculate_weighted_xfy(file_path_c + 'cl_phr_big_chunk_cut_type_xfy.txt', file_path_c + 'cl_phr_big_chunk_cut_type_xfy_weighted.txt', weighted_avg_limit_clause)

def phrase_big_chunk_chunk_cut(a_treebank, weighted_avg_limit_phrase, file_path_phrase3, k):

    print('phrase_big_chunk_chunk_cut')
    big_chunk_n = 0  # number of lds within phrase
    chunk_n = 0  # number of chunks

    #tokens
    with open(file_path_phrase3 + 'phr_big_chunk_chunk_cut.txt', mode='w', encoding='utf-8') as output:
        print('sent_id' + '\t' + 'clause_text' + '\t' + 'phrase_text' + '\t' + 'big_chunk_n' + '\t' + 'big_chunk_text' + '\t' + 'chunk_n' + '\t' + 'chunk_text', file=output)

        for sentence in a_treebank.sentence_list:
            podminka = k == 'bez_conj_a_cond' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj == 0
            podminka2 = k == 'bez_cond' and sentence.root_good and not sentence.bad_things and not sentence.condicional
            podminka3 = k == 'jen_filtr' and sentence.root_good and not sentence.bad_things
            podminka4 = k == 'bez_cond_conj1' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj <= 1
            podminka5 = k == 'bez_conj' and sentence.root_good and not sentence.bad_things and sentence.num_conj == 0
            podminka6 = k == 'bez_conj1' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 1
            podminka7 = k == 'bez_cond_conj2' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj <= 2
            podminka8 = k == 'bez_conj2' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 2
            podminka9 = k == 'bez_cond_conj3' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj <= 3
            podminka10 = k == 'bez_conj3' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 3
            if podminka or podminka2 or podminka3 or podminka4 or podminka5 or podminka6 or podminka7 or podminka8 or podminka9 or podminka10:
                for mainclause in sentence.main_clause_list:
                    for clause in mainclause.clause_list:
                        for phrase in clause.phrase_list:
                            big_chunks = []
                            chunks = []
                            for big_chunk in phrase.big_chunk_list:
                                big_chunk_n += 1
                                big_chunks.append(big_chunk.word_form)
                                for chunk in big_chunk.chunk_list:
                                    chunk_n += 1
                                    chunks.append(chunk.word_form)
                            print(sentence.id + '\t' + clause.word_form + '\t' + phrase.word_form + '\t' + str(big_chunk_n) + '\t' + ';'.join(big_chunks) + '\t' + str(chunk_n)+ '\t' + ';'.join(chunks), file=output)
                            big_chunk_n = 0
                            chunk_n = 0
            else:
                continue

        calculate_xfy(file_path_phrase3 + 'phr_big_chunk_chunk_cut.txt', file_path_phrase3 + 'phr_big_chunk_chunk_cut_xfy.txt', 'big_chunk_n', 'chunk_n')
        calculate_weighted_xfy(file_path_phrase3 + 'phr_big_chunk_chunk_cut_xfy.txt', file_path_phrase3 + 'phr_big_chunk_chunk_cut_xfy_weighted.txt', weighted_avg_limit_phrase)

        # types
        process_types(file_path_phrase3 + 'phr_big_chunk_chunk_cut.txt', file_path_phrase3 + 'phr_big_chunk_chunk_cut_type.txt', 'phrase_text')
        calculate_xfy(file_path_phrase3 + 'phr_big_chunk_chunk_cut_type.txt', file_path_phrase3 + 'phr_big_chunk_chunk_cut_type_xfy.txt', 'big_chunk_n', 'chunk_n')
        calculate_weighted_xfy(file_path_phrase3 + 'phr_big_chunk_chunk_cut_type_xfy.txt', file_path_phrase3 + 'phr_big_chunk_chunk_cut_type_xfy_weighted.txt', weighted_avg_limit_phrase)

def phrase_big_chunk_chunk_cut2(a_treebank, weighted_avg_limit_phrase, file_path_phrase3, k):

    print('phrase_big_chunk_chunk_cut2')
    big_chunk_n = 0  # number of lds within phrase
    chunk_n = 0  # number of chunks

    #tokens
    with open(file_path_phrase3 + 'phr_big_chunk_chunk2_cut.txt', mode='w', encoding='utf-8') as output:
        print('sent_id' + '\t' + 'clause_text' + '\t' + 'phrase_text' + '\t' + 'big_chunk_n' + '\t' + 'big_chunk_text' + '\t' + 'chunk_n' + '\t' + 'chunk_text', file=output)

        for sentence in a_treebank.sentence_list:
            podminka = k == 'bez_conj_a_cond' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj == 0
            podminka2 = k == 'bez_cond' and sentence.root_good and not sentence.bad_things and not sentence.condicional
            podminka3 = k == 'jen_filtr' and sentence.root_good and not sentence.bad_things
            podminka4 = k == 'bez_cond_conj1' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj <= 1
            podminka5 = k == 'bez_conj' and sentence.root_good and not sentence.bad_things and sentence.num_conj == 0
            podminka6 = k == 'bez_conj1' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 1
            podminka7 = k == 'bez_cond_conj2' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj <= 2
            podminka8 = k == 'bez_conj2' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 2
            podminka9 = k == 'bez_cond_conj3' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj <= 3
            podminka10 = k == 'bez_conj3' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 3
            if podminka or podminka2 or podminka3 or podminka4 or podminka5 or podminka6 or podminka7 or podminka8 or podminka9 or podminka10:
                for mainclause in sentence.main_clause_list:
                    for clause in mainclause.clause_list:
                        for phrase in clause.phrase_list:
                            big_chunks = []
                            chunks = []
                            for big_chunk in phrase.big_chunk_list:
                                big_chunk_n += 1
                                big_chunks.append(big_chunk.word_form)
                                for chunk in big_chunk.chunk2_list:
                                    chunk_n += 1
                                    chunks.append(chunk.word_form)
                            print(sentence.id + '\t' + clause.word_form + '\t' + phrase.word_form + '\t' + str(big_chunk_n) + '\t' + ';'.join(big_chunks) + '\t' + str(chunk_n)+ '\t' + ';'.join(chunks), file=output)
                            big_chunk_n = 0
                            chunk_n = 0
            else:
                continue

        calculate_xfy(file_path_phrase3 + 'phr_big_chunk_chunk2_cut.txt', file_path_phrase3 + 'phr_big_chunk_chunk2_cut_xfy.txt', 'big_chunk_n', 'chunk_n')
        calculate_weighted_xfy(file_path_phrase3 + 'phr_big_chunk_chunk2_cut_xfy.txt', file_path_phrase3 + 'phr_big_chunk_chunk2_cut_xfy_weighted.txt', weighted_avg_limit_phrase)

        # types
        process_types(file_path_phrase3 + 'phr_big_chunk_chunk2_cut.txt', file_path_phrase3 + 'phr_big_chunk_chunk2_cut_type.txt', 'phrase_text')
        calculate_xfy(file_path_phrase3 + 'phr_big_chunk_chunk2_cut_type.txt', file_path_phrase3 + 'phr_big_chunk_chunk2_cut_type_xfy.txt', 'big_chunk_n', 'chunk_n')
        calculate_weighted_xfy(file_path_phrase3 + 'phr_big_chunk_chunk2_cut_type_xfy.txt', file_path_phrase3 + 'phr_big_chunk_chunk2_cut_type_xfy_weighted.txt', weighted_avg_limit_phrase)

def big_chunk_chunk_word_cut(a_treebank, weighted_avg_limit_big_chunk, file_path_big_chunk3, k):

    print('big_chunk_chunk_word_cut')
    chunk_n = 0  # number of lds within phrase
    word_n = 0  # number of words in lds

    #tokens
    with open(file_path_big_chunk3 + 'big_chunk_chunk_w_cut.txt', mode='w', encoding='utf-8') as output:
        print('sent_id' + '\t' + 'clause_text' + '\t' + 'sentence_text' + '\t' + 'big_chunk_text' + '\t' + 'chunk_n' + '\t' + 'chunk_text' + '\t' + 'word_n', file=output)  # header

        for sentence in a_treebank.sentence_list:
            podminka = k == 'bez_conj_a_cond' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj == 0
            podminka2 = k == 'bez_cond' and sentence.root_good and not sentence.bad_things and not sentence.condicional
            podminka3 = k == 'jen_filtr' and sentence.root_good and not sentence.bad_things
            podminka4 = k == 'bez_cond_conj1' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj <= 1
            podminka5 = k == 'bez_conj' and sentence.root_good and not sentence.bad_things and sentence.num_conj == 0
            podminka6 = k == 'bez_conj1' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 1
            podminka7 = k == 'bez_cond_conj2' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj <= 2
            podminka8 = k == 'bez_conj2' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 2
            podminka9 = k == 'bez_cond_conj3' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj <= 3
            podminka10 = k == 'bez_conj3' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 3
            if podminka or podminka2 or podminka3 or podminka4 or podminka5 or podminka6 or podminka7 or podminka8 or podminka9 or podminka10:
                for mainclause in sentence.main_clause_list:
                    for clause in mainclause.clause_list:
                        for phrase in clause.phrase_list:
                            for big_chunk in phrase.big_chunk_list:
                                chunks = []
                                for chunk in big_chunk.chunk_list:
                                    chunk_n += 1
                                    chunks.append(chunk.word_form)
                                    for word in chunk.word_list:
                                        word_n += 1
                                print(sentence.id + '\t' + clause.word_form + '\t' + sentence.text + '\t' + big_chunk.word_form + '\t' + str(chunk_n) + '\t' + ';'.join(chunks) + '\t' + str(word_n), file=output)
                                chunk_n = 0
                                word_n = 0
            else:
                continue

        calculate_xfy(file_path_big_chunk3 + 'big_chunk_chunk_w_cut.txt', file_path_big_chunk3 + 'big_chunk_chunk_w_cut_xfy.txt', 'chunk_n', 'word_n')
        calculate_weighted_xfy(file_path_big_chunk3 + 'big_chunk_chunk_w_cut_xfy.txt', file_path_big_chunk3 + 'big_chunk_chunk_w_cut_xfy_weighted.txt', weighted_avg_limit_big_chunk)

        # types
        process_types(file_path_big_chunk3 + 'big_chunk_chunk_w_cut.txt', file_path_big_chunk3 + 'big_chunk_chunk_w_cut_type.txt', 'big_chunk_text')
        calculate_xfy(file_path_big_chunk3 + 'big_chunk_chunk_w_cut_type.txt', file_path_big_chunk3 + 'big_chunk_chunk_w_cut_type_xfy.txt', 'chunk_n', 'word_n')
        calculate_weighted_xfy(file_path_big_chunk3 + 'big_chunk_chunk_w_cut_type_xfy.txt', file_path_big_chunk3 + 'big_chunk_chunk_w_cut_type_xfy_weighted.txt', weighted_avg_limit_big_chunk)

def big_chunk_chunk_word_cut2(a_treebank, weighted_avg_limit_big_chunk, file_path_big_chunk3, k):

    print('big_chunk_chunk_word_cut2')
    chunk_n = 0  # number of lds within phrase
    word_n = 0  # number of words in lds

    #tokens
    with open(file_path_big_chunk3 + 'big_chunk_chunk_w2_cut.txt', mode='w', encoding='utf-8') as output:
        print('sent_id' + '\t' + 'clause_text' + '\t' + 'sentence_text' + '\t' + 'big_chunk_text' + '\t' + 'chunk_n' + '\t' + 'chunk_text' + '\t' + 'word_n', file=output)  # header

        for sentence in a_treebank.sentence_list:
            podminka = k == 'bez_conj_a_cond' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj == 0
            podminka2 = k == 'bez_cond' and sentence.root_good and not sentence.bad_things and not sentence.condicional
            podminka3 = k == 'jen_filtr' and sentence.root_good and not sentence.bad_things
            podminka4 = k == 'bez_cond_conj1' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj <= 1
            podminka5 = k == 'bez_conj' and sentence.root_good and not sentence.bad_things and sentence.num_conj == 0
            podminka6 = k == 'bez_conj1' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 1
            podminka7 = k == 'bez_cond_conj2' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj <= 2
            podminka8 = k == 'bez_conj2' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 2
            podminka9 = k == 'bez_cond_conj3' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj <= 3
            podminka10 = k == 'bez_conj3' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 3
            if podminka or podminka2 or podminka3 or podminka4 or podminka5 or podminka6 or podminka7 or podminka8 or podminka9 or podminka10:
                for mainclause in sentence.main_clause_list:
                    for clause in mainclause.clause_list:
                        for phrase in clause.phrase_list:
                            for big_chunk in phrase.big_chunk_list:
                                chunks = []
                                for chunk in big_chunk.chunk2_list:
                                    chunk_n += 1
                                    chunks.append(chunk.word_form)
                                    for word in chunk.word_list:
                                        word_n += 1
                                print(sentence.id + '\t' + clause.word_form + '\t' + sentence.text + '\t' + big_chunk.word_form + '\t' + str(chunk_n) + '\t' + ';'.join(chunks) + '\t' + str(word_n), file=output)
                                chunk_n = 0
                                word_n = 0
            else:
                continue

        calculate_xfy(file_path_big_chunk3 + 'big_chunk_chunk_w2_cut.txt', file_path_big_chunk3 + 'big_chunk_chunk_w2_cut_xfy.txt', 'chunk_n', 'word_n')
        calculate_weighted_xfy(file_path_big_chunk3 + 'big_chunk_chunk_w2_cut_xfy.txt', file_path_big_chunk3 + 'big_chunk_chunk_w2_cut_xfy_weighted.txt', weighted_avg_limit_big_chunk)

        # types
        process_types(file_path_big_chunk3 + 'big_chunk_chunk_w2_cut.txt', file_path_big_chunk3 + 'big_chunk_chunk_w2_cut_type.txt', 'big_chunk_text')
        calculate_xfy(file_path_big_chunk3 + 'big_chunk_chunk_w2_cut_type.txt', file_path_big_chunk3 + 'big_chunk_chunk_w2_cut_type_xfy.txt', 'chunk_n', 'word_n')
        calculate_weighted_xfy(file_path_big_chunk3 + 'big_chunk_chunk_w2_cut_type_xfy.txt', file_path_big_chunk3 + 'big_chunk_chunk_w2_cut_type_xfy_weighted.txt', weighted_avg_limit_big_chunk)

def chunk_word_syllable_cut(a_treebank, weighted_avg_limit_chunk, file_path_chunk, k):

    print('chunk_word_syllable')
    word_n = 0  # number of lds within phrase
    syllable_n = 0  # number of syllables in lds

    #tokens
    with open(file_path_chunk + 'chunk_word_syl_cut.txt', mode='w', encoding='utf-8') as output:
        print('sent_id' + '\t' + 'clause_text' + '\t' + 'sentence_text' + '\t' + 'chunk_text' + '\t' + 'word_n' + '\t' + 'syllable_n', file=output)  # header

        for sentence in a_treebank.sentence_list:
            podminka = k == 'bez_conj_a_cond' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj == 0
            podminka2 = k == 'bez_cond' and sentence.root_good and not sentence.bad_things and not sentence.condicional
            podminka3 = k == 'jen_filtr' and sentence.root_good and not sentence.bad_things
            podminka4 = k == 'bez_cond_conj1' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj <= 1
            podminka5 = k == 'bez_conj' and sentence.root_good and not sentence.bad_things and sentence.num_conj == 0
            podminka6 = k == 'bez_conj1' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 1
            podminka7 = k == 'bez_cond_conj2' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj <= 2
            podminka8 = k == 'bez_conj2' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 2
            podminka9 = k == 'bez_cond_conj3' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj <= 3
            podminka10 = k == 'bez_conj3' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 3
            if podminka or podminka2 or podminka3 or podminka4 or podminka5 or podminka6 or podminka7 or podminka8 or podminka9 or podminka10:
                for mainclause in sentence.main_clause_list:
                    for clause in mainclause.clause_list:
                        for phrase in clause.phrase_list:
                            for big_chunk in phrase.big_chunk_list:
                                for chunk in big_chunk.chunk_list:
                                    words = []
                                    for word in chunk.word_list:
                                        word_n += 1
                                        words.append(word.form)
                                        syllable_n += word.num_syllab
                                    print(sentence.id + '\t' + clause.word_form + '\t' + sentence.text + '\t' + chunk.word_form + '\t' + str(word_n) + '\t' + str(syllable_n), file=output)
                                    word_n = 0
                                    syllable_n = 0
            else:
                continue

        calculate_xfy(file_path_chunk + 'chunk_word_syl_cut.txt', file_path_chunk + 'chunk_word_syl_cut_xfy.txt', 'word_n', 'syllable_n')
        calculate_weighted_xfy(file_path_chunk + 'chunk_word_syl_cut_xfy.txt', file_path_chunk + 'chunk_word_syl_cut_xfy_weighted.txt', weighted_avg_limit_chunk)

        # types
        process_types(file_path_chunk + 'chunk_word_syl_cut.txt', file_path_chunk + 'chunk_word_syl_cut_type.txt', 'chunk_text')
        calculate_xfy(file_path_chunk + 'chunk_word_syl_cut_type.txt', file_path_chunk + 'chunk_word_syl_cut_type_xfy.txt', 'word_n', 'syllable_n')
        calculate_weighted_xfy(file_path_chunk + 'chunk_word_syl_cut_type_xfy.txt', file_path_chunk + 'chunk_word_syl_cut_type_xfy_weighted.txt', weighted_avg_limit_chunk)

def chunk_word_syllable_cut2(a_treebank, weighted_avg_limit_chunk, file_path_chunk, k):

    print('chunk_word_syllable2')
    word_n = 0  # number of lds within phrase
    syllable_n = 0  # number of syllables in lds

    #tokens
    with open(file_path_chunk + 'chunk_word_syl2_cut.txt', mode='w', encoding='utf-8') as output:
        print('sent_id' + '\t' + 'clause_text' + '\t' + 'sentence_text' + '\t' + 'chunk_text' + '\t' + 'word_n' + '\t' + 'syllable_n', file=output)  # header

        for sentence in a_treebank.sentence_list:
            podminka = k == 'bez_conj_a_cond' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj == 0
            podminka2 = k == 'bez_cond' and sentence.root_good and not sentence.bad_things and not sentence.condicional
            podminka3 = k == 'jen_filtr' and sentence.root_good and not sentence.bad_things
            podminka4 = k == 'bez_cond_conj1' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj <= 1
            podminka5 = k == 'bez_conj' and sentence.root_good and not sentence.bad_things and sentence.num_conj == 0
            podminka6 = k == 'bez_conj1' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 1
            podminka7 = k == 'bez_cond_conj2' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj <= 2
            podminka8 = k == 'bez_conj2' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 2
            podminka9 = k == 'bez_cond_conj3' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj <= 3
            podminka10 = k == 'bez_conj3' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 3
            if podminka or podminka2 or podminka3 or podminka4 or podminka5 or podminka6 or podminka7 or podminka8 or podminka9 or podminka10:
                for mainclause in sentence.main_clause_list:
                    for clause in mainclause.clause_list:
                        for phrase in clause.phrase_list:
                            for big_chunk in phrase.big_chunk_list:
                                for chunk in big_chunk.chunk2_list:
                                    words = []
                                    for word in chunk.word_list:
                                        word_n += 1
                                        words.append(word.form)
                                        syllable_n += word.num_syllab
                                    print(sentence.id + '\t' + clause.word_form + '\t' + sentence.text + '\t' + chunk.word_form + '\t' + str(word_n) + '\t' + str(syllable_n), file=output)
                                    word_n = 0
                                    syllable_n = 0
            else:
                continue

        calculate_xfy(file_path_chunk + 'chunk_word_syl2_cut.txt', file_path_chunk + 'chunk_word_syl2_cut_xfy.txt', 'word_n', 'syllable_n')
        calculate_weighted_xfy(file_path_chunk + 'chunk_word_syl2_cut_xfy.txt', file_path_chunk + 'chunk_word_syl2_cut_xfy_weighted.txt', weighted_avg_limit_chunk)

        # types
        process_types(file_path_chunk + 'chunk_word_syl2_cut.txt', file_path_chunk + 'chunk_word_syl2_cut_type.txt', 'chunk_text')
        calculate_xfy(file_path_chunk + 'chunk_word_syl2_cut_type.txt', file_path_chunk + 'chunk_word_syl2_cut_type_xfy.txt', 'word_n', 'syllable_n')
        calculate_weighted_xfy(file_path_chunk + 'chunk_word_syl2_cut_type_xfy.txt', file_path_chunk + 'chunk_word_syl2_cut_type_xfy_weighted.txt', weighted_avg_limit_chunk)

def word_syllable_char_cut(a_treebank, weighted_avg_limit_word, file_path_w, k):

    print('word_syllab_char')

    # tokens
    with open(file_path_w + 'word_syl_char_cut.txt', mode='w', encoding='utf-8') as output:
        print('sent_id' + '\t' + 'slovo' + '\t' + 'phoneme_word' + '\t' + 'syllab_CV' + '\t' + 'syllable_n' + '\t' + 'char_n', file=output)  # header

        for sentence in a_treebank.sentence_list:
            podminka = k == 'bez_conj_a_cond' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj == 0
            podminka2 = k == 'bez_cond' and sentence.root_good and not sentence.bad_things and not sentence.condicional
            podminka3 = k == 'jen_filtr' and sentence.root_good and not sentence.bad_things
            podminka4 = k == 'bez_cond_conj1' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj <= 1
            podminka5 = k == 'bez_conj' and sentence.root_good and not sentence.bad_things and sentence.num_conj == 0
            podminka6 = k == 'bez_conj1' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 1
            podminka7 = k == 'bez_cond_conj2' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj <= 2
            podminka8 = k == 'bez_conj2' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 2
            podminka9 = k == 'bez_cond_conj3' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj <= 3
            podminka10 = k == 'bez_conj3' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 3
            if podminka or podminka2 or podminka3 or podminka4 or podminka5 or podminka6 or podminka7 or podminka8 or podminka9 or podminka10:
                for mainclause in sentence.main_clause_list:
                    for clause in mainclause.clause_list:
                        for phrase in clause.phrase_list:
                            for big_chunk in phrase.big_chunk_list:
                                for chunk in big_chunk.chunk_list:
                                    for word in chunk.word_list:
                                        char_n = len(word.phoneme_word)
                                        print(sentence.id + '\t' + word.form + '\t' + word.phoneme_word + '\t' + word.prepis_CV + '\t' + str(word.num_syllab) + '\t' + str(char_n), file=output)
            else:
                continue

    calculate_xfy(file_path_w + 'word_syl_char_cut.txt', file_path_w + 'word_syl_char_cut_xfy.txt', 'syllable_n', 'char_n')
    calculate_weighted_xfy(file_path_w + 'word_syl_char_cut_xfy.txt', file_path_w + 'word_syl_char_cut_xfy_weighted.txt', weighted_avg_limit_word)

    # types
    process_types(file_path_w + 'word_syl_char_cut.txt', file_path_w + 'word_syl_char_cut_type.txt', 'phoneme_word')
    calculate_xfy(file_path_w + 'word_syl_char_cut_type.txt', file_path_w + 'word_syl_char_cut_type_xfy.txt', 'syllable_n', 'char_n')
    calculate_weighted_xfy(file_path_w + 'word_syl_char_cut_type_xfy.txt', file_path_w + 'word_syl_char_cut_type_xfy_weighted.txt', weighted_avg_limit_word)

def word_syllable_char_cut(a_treebank, weighted_avg_limit_word, file_path_w, k):

    print('word_syllab_char')

    # tokens
    with open(file_path_w + 'word_syl_char_cut.txt', mode='w', encoding='utf-8') as output:
        print('sent_id' + '\t' + 'slovo' + '\t' + 'phoneme_word' + '\t' + 'syllab_CV' + '\t' + 'syllable_n' + '\t' + 'char_n', file=output)  # header

        for sentence in a_treebank.sentence_list:
            podminka = k == 'bez_conj_a_cond' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj == 0
            podminka2 = k == 'bez_cond' and sentence.root_good and not sentence.bad_things and not sentence.condicional
            podminka3 = k == 'jen_filtr' and sentence.root_good and not sentence.bad_things
            podminka4 = k == 'bez_cond_conj1' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj <= 1
            podminka5 = k == 'bez_conj' and sentence.root_good and not sentence.bad_things and sentence.num_conj == 0
            podminka6 = k == 'bez_conj1' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 1
            podminka7 = k == 'bez_cond_conj2' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj <= 2
            podminka8 = k == 'bez_conj2' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 2
            podminka9 = k == 'bez_cond_conj3' and sentence.root_good and not sentence.bad_things and not sentence.condicional and sentence.num_conj <= 3
            podminka10 = k == 'bez_conj3' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 3
            if podminka or podminka2 or podminka3 or podminka4 or podminka5 or podminka6 or podminka7 or podminka8 or podminka9 or podminka10:
                for mainclause in sentence.main_clause_list:
                    for clause in mainclause.clause_list:
                        for phrase in clause.phrase_list:
                            for big_chunk in phrase.big_chunk_list:
                                for chunk in big_chunk.chunk_list:
                                    for word in chunk.word_list:
                                        char_n = len(word.phoneme_word)
                                        print(sentence.id + '\t' + word.form + '\t' + word.phoneme_word + '\t' + word.prepis_CV + '\t' + str(word.num_syllab) + '\t' + str(char_n), file=output)
            else:
                continue

    calculate_xfy(file_path_w + 'word_syl_char_cut.txt', file_path_w + 'word_syl_char_cut_xfy.txt', 'syllable_n', 'char_n')
    calculate_weighted_xfy(file_path_w + 'word_syl_char_cut_xfy.txt', file_path_w + 'word_syl_char_cut_xfy_weighted.txt', weighted_avg_limit_word)

    # types
    process_types(file_path_w + 'word_syl_char_cut.txt', file_path_w + 'word_syl_char_cut_type.txt', 'phoneme_word')
    calculate_xfy(file_path_w + 'word_syl_char_cut_type.txt', file_path_w + 'word_syl_char_cut_type_xfy.txt', 'syllable_n', 'char_n')
    calculate_weighted_xfy(file_path_w + 'word_syl_char_cut_type_xfy.txt', file_path_w + 'word_syl_char_cut_type_xfy_weighted.txt', weighted_avg_limit_word)


def get_info(a_treebank, file_path, k, name):

    sentence_n = 0
    main_clause_n = 0
    clause_n = 0
    phrase_n = 0
    big_chunk_n = 0
    chunk_n  = 0
    chunk2_n = 0
    word_n = 0

    for sentence in a_treebank.sentence_list:
        podminka = k == 'bez_conj1' and sentence.root_good and not sentence.bad_things and sentence.num_conj <= 1
        if podminka:
            sentence_n += 1
            for mainclause in sentence.main_clause_list:
                main_clause_n += 1
                for clause in mainclause.clause_list:
                    clause_n += 1
                    for phrase in clause.phrase_list:
                        phrase_n += 1
                        for bigchunk in phrase.big_chunk_list:
                            big_chunk_n += 1
                            for chunk in bigchunk.chunk_list:
                                chunk_n += 1
                                for word in chunk.word_list:
                                    word_n += 1
                            for chunk2 in bigchunk.chunk2_list:
                                chunk2_n += 1
        else:
            continue

    with open(file_path + "/" + name + '_text_overview.txt', mode='w', encoding='utf-8') as data_to_write:
        print('sentence_n\tmain_clause_n\tclause_n\tphrase_n\tsubphrase_n\tchunk_n\tchunk2_n\tword_n', file=data_to_write)
        print(f'{sentence_n}\t{main_clause_n}\t{clause_n}\t{phrase_n}\t{big_chunk_n}\t{chunk_n}\t{chunk2_n}\t{word_n}', file=data_to_write)

def load_xfy_file(input_file):
    """loads xfy data and creates their list,
       x==construct lengths, f(x)==their frequencies, y==constituent lengths"""

    data_list = []

    with open(input_file, mode='r', encoding='utf-8') as input:
        for line in input:
            data_list.append(line.split('\t'))

    return data_list


def prepare_program_file(input_file, program_file, model):
    """creates two program files to be run by NLREG, one for truncated formula, one for complete formula"""

    # load variables including header!
    data_list = load_xfy_file(input_file)

    if model == 'truncated':
        variable = 'Variables x,y;'
        parameter_truncated = 'Parameter b;'  # parameter a == an empirically obtained value
        # xfy data file contains a header, hence, index starts with 1 to exclude the header
        constant = 'Constant firstConstr = ' + data_list[1][2].strip() + ';'
        #function_truncated = 'Function y = firstConstr * (x^b);'
        function_truncated = 'Function y = (firstConstr - 1) * (x^b) + 1;'
        #function_truncated = 'Function y = (firstConstr - c) * (x^(-b)) + c;'
        #function_truncated = 'Function y = firstConstr * (x^(-b));'
        data = 'data;'

        # truncated model
        with open(program_file, mode='w', encoding='utf-8') as output:
            print(variable, file=output)
            print(parameter_truncated, file=output)
            print(constant, file=output)
            print(function_truncated, file=output)
            print(data, file=output)
            # xfy data file contains a header, hence, index starts with 1 to exclude the header
            for index in range(1, len(data_list)):
                print(data_list[index][0] + '\t' + data_list[index][2], end='', file=output)

    if model == 'c':

        variable = 'Variables x,y;'
        parameter_truncated = 'Parameter b, c;'  # parameter a == an empirically obtained value
        # xfy data file contains a header, hence, index starts with 1 to exclude the header
        constant = 'Constant firstConstr = ' + data_list[1][2].strip() + ';'
        # function_truncated = 'Function y = firstConstr * (x^b);'
        # function_truncated = 'Function y = (firstConstr - 1) * (x^b) + 1;'
        function_c = 'Function y = (firstConstr - c) * (x^(-b)) + c;'
        # function_truncated = 'Function y = firstConstr * (x^(-b));'
        data = 'data;'

        # truncated model
        with open(program_file, mode='w', encoding='utf-8') as output:
            print(variable, file=output)
            print(parameter_truncated, file=output)
            print(constant, file=output)
            print(function_c, file=output)
            print(data, file=output)
            # xfy data file contains a header, hence, index starts with 1 to exclude the header
            for index in range(1, len(data_list)):
                print(data_list[index][0] + '\t' + data_list[index][2], end='', file=output)


def run_nlreg_MAL(input_file, model):
    """creates names for nlr and lst files and run NLREG using cmd line"""

    input_file_split = input_file.split('.')

    if model == 'truncated':

        truncated_program_file = input_file_split[0] + "_truncated.nlr"
        prepare_program_file(input_file, truncated_program_file, model)
        print(truncated_program_file.split('.')[0])
        nlreg_truncated_output = truncated_program_file.split('.')[0] + '_nlreg.lst'

        run(['C:/Users/nogol/Documents/Doktorat/NLREG/NLREGCA.exe', truncated_program_file, '/list', nlreg_truncated_output])

    if model == 'c':

        c_program_file = input_file_split[0] + "_c.nlr"
        prepare_program_file(input_file, c_program_file, model)
        nlreg_c_output = c_program_file.split('.')[0] + '_nlreg.lst'

        run(['C:/Users/nogol/Documents/Doktorat/NLREG/NLREGCA.exe', c_program_file, '/list', nlreg_c_output])


def process_lst_files_MAL(output_folder, model, output_csv=None):
    """Processes NLREG output files (.lst) in the specified output folder and optionally saves the result as a CSV file."""

    if model == 'truncated':

        # Function to classify the file based on part of the name
        def classify_file(filename):
            if "type_xfy_truncated" in filename:
                return "type_xfy_truncated"
            elif "type_xfy_weighted" in filename:
                return "type_xfy_weighted"
            elif "cut_xfy_truncated" in filename:
                return "cut_xfy_truncated"
            elif "cut_xfy_weighted" in filename:
                return "cut_xfy_weighted"
            return None

        # Initialize a dictionary to hold data for each group
        grouped_data = {
            "type_xfy_truncated": [],
            "type_xfy_weighted": [],
            "cut_xfy_truncated": [],
            "cut_xfy_weighted": []
        }

        # Iterate through files and classify them
        for filename in os.listdir(output_folder):
            if filename.endswith(".lst"):
                category = classify_file(filename)
                if category:
                    file_path = os.path.join(output_folder, filename)
                    data = extract_info_from_lst_MAL(file_path, model)
                    data['firstConstr'] = get_first_constr_MAL(file_path)
                    data['File Name'] = filename
                    grouped_data[category].append(data)

        # Store DataFrames if you want to return all
        all_dfs = {}

        # Create CSV files for each group
        for category, files_data in grouped_data.items():
            if files_data:
                # Add Parametr b and potentially Parametr c for the 'c' model
                columns = ['File Name', 'R^2', 'firstConstr', 'Parameter b']

                # Create DataFrame with the correct columns
                df = pd.DataFrame(files_data, columns=columns)

                # Reorder based on desired order and then sort by 'File Name'
                # df['Category'] = df['File Name'].apply(
                #     lambda x: next((order for order in desired_order if order in x), None))
                # df = df.dropna(subset=['Category'])  # Drop files that don't match desired order
                df['Category'] = df['File Name'].str.split('_cut').str[0]
                #df = df.set_index('Category').loc[desired_order].reset_index()  # Reorder by desired order

                # Drop the 'File Name' column
                df = df.drop(columns=['File Name'])

                # Save to CSV if output path is provided
                if output_csv:
                    output_path = os.path.join(output_csv, f'01NLREG_MAL_info_{model}_{category}.csv')
                    df.to_csv(output_path, index=False)

                # Collect DataFrame for return
                all_dfs[category] = df

        return all_dfs

    if model == 'c':
        # Function to classify the file based on part of the name
        def classify_file(filename):
            if "type_xfy_c" in filename:
                return "type_xfy_c"
            elif "type_xfy_weighted_c" in filename:
                return "type_xfy_weighted_c"
            elif "cut_xfy_c" in filename:
                return "cut_xfy_c"
            elif "cut_xfy_weighted_c" in filename:
                return "cut_xfy_weighted_c"
            return None


        # Initialize a dictionary to hold data for each group
        grouped_data = {
            "type_xfy_c": [],
            "type_xfy_weighted_c": [],
            "cut_xfy_c": [],
            "cut_xfy_weighted_c": []
        }

        # Iterate through files and classify them
        for filename in os.listdir(output_folder):
            if filename.endswith(".lst"):
                category = classify_file(filename)
                if category:
                    file_path = os.path.join(output_folder, filename)
                    data = extract_info_from_lst_MAL(file_path, model)
                    data['firstConstr'] = get_first_constr_MAL(file_path)
                    data['File Name'] = filename
                    grouped_data[category].append(data)

        # Store DataFrames if you want to return all
        all_dfs = {}

        # Create CSV files for each group
        for category, files_data in grouped_data.items():
            if files_data:
                # Add Parametr b and potentially Parametr c for the 'c' model
                columns = ['File Name', 'R^2', 'firstConstr', 'Parameter b', 'Parameter c']

                # Create DataFrame with the correct columns
                df = pd.DataFrame(files_data, columns=columns)

                # Reorder based on desired order and then sort by 'File Name'
                #df['Category'] = df['File Name'].apply(
                    #lambda x: next((order for order in desired_order if order in x), None))
                #df = df.dropna(subset=['Category'])  # Drop files that don't match desired order
                df['Category'] = df['File Name'].str.split('_cut').str[0]
                #df = df.set_index('Category').loc[desired_order].reset_index()  # Reorder by desired order


                df = df.drop(columns=['File Name'])

                # Save to CSV if output path is provided
                if output_csv:
                    output_path = os.path.join(output_csv, f'01NLREG_MAL_info_{model}_{category}.csv')
                    df.to_csv(output_path, index=False)

                # Collect DataFrame for return
                all_dfs[category] = df

def extract_info_from_lst_MAL(lst_file, model):
    """Extracts information from a single NLREG output file (.lst)."""

    if model == 'truncated':
        with open(lst_file, 'r') as file:
            lines = file.readlines()

        r_squared_line = [line for line in lines if line.startswith('Proportion of variance explained (R^2)')]
        parameter_b_line = [line for line in lines if line.startswith('         b')]

        if r_squared_line and parameter_b_line:
            r_squared = r_squared_line[0].split('=')[1].split('(')[0].strip()
            parameter_b = parameter_b_line[0].split()[2]
            return {'File Name': os.path.basename(lst_file), 'R^2': r_squared, 'Parameter b': parameter_b}

        return {'File Name': os.path.basename(lst_file), 'R^2': 'None', 'Parameter b': 'None', 'Parameter c': 'None'}

    if model == 'c':
        with open(lst_file, 'r') as file:
            lines = file.readlines()

        r_squared_line = [line for line in lines if line.startswith('Proportion of variance explained (R^2)')]
        parameter_b_line = [line for line in lines if line.startswith('         b')]
        parameter_c_line = [line for line in lines if line.startswith('         c')]
        # print(parameter_c_line)
        # print(parameter_b_line)

        if r_squared_line and parameter_b_line and parameter_c_line:
            r_squared = r_squared_line[0].split('=')[1].split('(')[0].strip()
            parameter_b = parameter_b_line[0].split()[2]
            parameter_c = parameter_c_line[0].split()[2]
            return {'File Name': os.path.basename(lst_file), 'R^2': r_squared, 'Parameter b': parameter_b,
                    'Parameter c': parameter_c}
        elif r_squared_line and parameter_b_line:
            r_squared = r_squared_line[0].split('=')[1].split('(')[0].strip()
            parameter_b = parameter_b_line[0].split()[2]
            return {'File Name': os.path.basename(lst_file), 'R^2': r_squared, 'Parameter b': parameter_b,
                    'Parameter c': 'None'}

        return {'File Name': os.path.basename(lst_file), 'R^2': 'None', 'Parameter b': 'None', 'Parameter c': 'None'}



def copy_lst_files(source_dirs, destination_dir, treebank, model):
    """
    Copies all .lst files from the specified source directories to the destination directory.

    Parameters:
    source_dirs (list of str): List of paths to the source directories.
    destination_dir (str): Path to the destination directory.
    """
    if model == 'truncated':
        print('Starts with copying truncated.lst files')

        if not os.path.exists(destination_dir):
            os.makedirs(destination_dir)

        for source_dir in source_dirs:
            if os.path.exists(source_dir):
                for file_name in os.listdir(source_dir):
                    if file_name.endswith('_truncated_nlreg.lst'):
                        source_file = os.path.join(source_dir, file_name)
                        destination_file = destination_dir + treebank + '_' + file_name
                        shutil.copy(source_file, destination_file)
                        #print(f"Copied {source_file} to {destination_file}")
            else:
                print(f"Source directory {source_dir} does not exist")

    if model == 'c':
        print('Starts with copying c.lst files')

        if not os.path.exists(destination_dir):
            os.makedirs(destination_dir)

        for source_dir in source_dirs:
            if os.path.exists(source_dir):
                for file_name in os.listdir(source_dir):
                    if file_name.endswith('_c_nlreg.lst'):
                        source_file = os.path.join(source_dir, file_name)
                        destination_file = destination_dir + treebank + '_' + file_name
                        shutil.copy(source_file, destination_file)
                        # print(f"Copied {source_file} to {destination_file}")
            else:
                print(f"Source directory {source_dir} does not exist")


def get_first_constr_MAL(lst_file):
    """Extracts the value of firstConstr from a single NLREG output file (.lst)."""
    # Implement the code to extract the firstConstr value from the .lst file
    # and return it as a string or None if not found.

    with open(lst_file, 'r') as file:
        lines = file.readlines()

    for line in lines:
        if line.startswith('   3: Constant firstConstr = '):
            first_constr = line.split('=')[1].strip().rstrip(';')
            return first_constr

    return None

# Function to read data from a file
def read_data(file_path):
    if os.path.exists(file_path):
        return pd.read_csv(file_path, sep=',', header=0)
    else:
        print(f"File not found: {file_path}")
        return pd.DataFrame()

def read_data_txt(file_path):
    if os.path.exists(file_path):
        return pd.read_csv(file_path, sep='\t', header=0)
    else:
        print(f"File not found: {file_path}")
        return pd.DataFrame()

# Function to concatenate aligned DataFrames with spacing columns
def concatenate_with_spacing(dataframes, spacing_cols=3):
    """
    Concatenates aligned DataFrames and adds spacing columns (filled with NaN) between them.
    """
    spacing_df = pd.DataFrame(columns=[''] * spacing_cols)  # Create spacing columns
    concatenated_df = dataframes[0]

    for i, df in enumerate(dataframes[1:]):
        concatenated_df = pd.concat([concatenated_df, spacing_df, df], axis=1)

    return concatenated_df

# Updated construct processing logic
def process_construct_files(construct_files, levels):
    construct_csvs = {i: pd.DataFrame() for i in range(1, 8)}
    clause_levels = ['cl_phr_big_chunk']
    phrase_levels = ['phr_big_chunk_chunk',  'phr_big_chunk_chunk2']
    big_chunk_levels = ['big_chunk_chunk_w', 'big_chunk_chunk_w2']
    unit_levels = ['chunk_word_syl', 'chunk_word_syl2']
    #word_syllable_levels = ['big_chunk_w_syl', 'big_chunk_w_syl2']

    # Process levels
    for i, level_set in enumerate(
            [['sen_maincl_cl'], ['maincl_cl_phr'], ['cl_phr_big_chunk'], phrase_levels, big_chunk_levels,
             unit_levels, ['word_syl_char']], start=1):
        dataframes_to_concatenate = []

        for level in level_set:
            type_file = construct_files[level]['type']
            token_file = construct_files[level]['token']

            type_data = read_data_txt(type_file)
            token_data = read_data_txt(token_file)

            type_data["construct"] = pd.to_numeric(type_data["construct"], downcast='integer', errors='coerce')
            token_data["construct"] = pd.to_numeric(token_data["construct"], downcast='integer', errors='coerce')

            type_data["avg_constituent_len"] = type_data["avg_constituent_len"].apply(lambda x: round(x, 3))
            token_data["avg_constituent_len"] = token_data["avg_constituent_len"].apply(lambda x: round(x, 3))

            # Add to list for alignment
            dataframes_to_concatenate.extend([type_data, token_data])

        # Concatenate with spacing columns
        construct_csvs[i] = concatenate_with_spacing(dataframes_to_concatenate)

    return construct_csvs


# Function to process R^2 data
def process_r2_data(truncated_type_data, truncated_token_data, c_type_data, c_token_data, lang):
    r2_csvs = {i: pd.DataFrame() for i in range(1, 8)}
    clause_levels = [lang + '_cl_phr_big_chunk', lang + '_cl_phr_big_chunk2']
    phrase_levels = [lang + '_phr_big_chunk_chunk', lang + '_phr_big_chunk_chunk2']
    big_chunk_levels = [lang + '_big_chunk_chunk_w', lang + '_big_chunk_chunk_w2']
    unit_levels = [lang +  '_chunk_word_syl', lang + '_chunk_word_syl2']
    #word_syllable_levels = [lang + '_big_chunk_w_syl', lang + '_big_chunk_w_syl2']

    # Process levels
    for i, level_set in enumerate([[lang + '_sen_maincl_cl'], [lang + '_maincl_cl_phr'], [lang + '_cl_phr_big_chunk'], phrase_levels, big_chunk_levels, unit_levels,[lang + '_word_syl_char']], start=1):
        for level in level_set:
            # Filter data
            truncated_type = truncated_type_data[truncated_type_data['Category'] == level].drop(columns=['Category'], errors='ignore')
            #print(truncated_type)
            truncated_token = truncated_token_data[truncated_token_data['Category'] == level].drop(columns=['Category'], errors='ignore')
            c_type = c_type_data[c_type_data['Category'] == level].drop(columns=['Category'], errors='ignore')
            c_token = c_token_data[c_token_data['Category'] == level].drop(columns=['Category'], errors='ignore')

            # Concatenate
            combined_type = pd.concat([truncated_type, c_type], ignore_index=True)
            combined_token = pd.concat([truncated_token, c_token], ignore_index=True)

            # Append to the R^2 CSV
            r2_csvs[i] = pd.concat([r2_csvs[i], combined_type, pd.DataFrame(columns=['', '']), combined_token, pd.DataFrame(columns=['', ''])], axis=1)

    return r2_csvs

# Main function to process all data
def main(path, lang_mat, kat, levels, weighted=False):
    suffix = "_weighted" if weighted else ""
    for lang in lang_mat:
        for k in kat:
            print(f"Processing: Language={lang}, Category={k}, Weighted={weighted}")
            construct_files = {l: {
                'type': f'{path}/{k}/{lang}/{l}/{l}_cut_type_xfy{suffix}.txt',
                'token': f'{path}/{k}/{lang}/{l}/{l}_cut_xfy{suffix}.txt'
            } for l in levels}

            if weighted:
                truncated_type_file = f'{path}/NLREG/truncated/{k}/{lang}/01NLREG_MAL_info_truncated_type_xfy{suffix}.csv'
                truncated_token_file = f'{path}/NLREG/truncated/{k}/{lang}/01NLREG_MAL_info_truncated_cut_xfy{suffix}.csv'
                c_type_file = f'{path}/NLREG/c/{k}/{lang}/01NLREG_MAL_info_c_type_xfy{suffix}_c.csv'
                c_token_file = f'{path}/NLREG/c/{k}/{lang}/01NLREG_MAL_info_c_cut_xfy{suffix}_c.csv'

            else:
                truncated_type_file = f'{path}/NLREG/truncated/{k}/{lang}/01NLREG_MAL_info_truncated_type_xfy_truncated.csv'
                truncated_token_file = f'{path}/NLREG/truncated/{k}/{lang}/01NLREG_MAL_info_truncated_cut_xfy_truncated.csv'
                c_type_file = f'{path}/NLREG/c/{k}/{lang}/01NLREG_MAL_info_c_type_xfy_c.csv'
                c_token_file = f'{path}/NLREG/c/{k}/{lang}/01NLREG_MAL_info_c_cut_xfy_c.csv'

            # Read R^2 data
            truncated_type_data = read_data(truncated_type_file)
            truncated_token_data = read_data(truncated_token_file)
            c_type_data = read_data(c_type_file)
            c_token_data = read_data(c_token_file)

            # Process construct and R^2 data
            construct_csvs = process_construct_files(construct_files, levels)
            #print(construct_csvs)
            r2_csvs = process_r2_data(truncated_type_data, truncated_token_data, c_type_data, c_token_data, lang)

            #print(r2_csvs)
            # Save to output
            output_path = f'{path}/vys_tab/{k}/{lang}/{"weighted" if weighted else "normal"}/'
            os.makedirs(output_path, exist_ok=True)
            with open(output_path + 'all_tables.txt', mode='w', encoding='utf-8') as output:
                output.write('#type' + '\t' + '\t' + '\t' + '\t' + '\t' + '\t' + '#token\n')
                output.write('sen_maincl_cl' + '\t' + '\t' + '\t' + '\t' + '\t' + '\t' + 'sen_maincl_cl\n')
                for i in range(1, 8):
                    if i == 1:
                        construct_csvs[i].to_csv(output, sep='\t', index=False, mode='w', lineterminator='\n')
                        output.write('\n')
                        r2_csvs[i].to_csv(output, sep='\t', index=False, mode='w', lineterminator='\n')
                        output.write('\n')
                    elif i == 2:
                        output.write('#type' + '\t' + '\t' + '\t' + '\t' + '\t' + '\t' + '#token\n')
                        output.write('maincl_cl_phr' + '\t' + '\t' + '\t' + '\t' + '\t' + '\t' + 'maincl_cl_phr\n')
                        construct_csvs[i].to_csv(output, sep='\t', index=False, mode='w', lineterminator='\n')
                        output.write('\n')
                        r2_csvs[i].to_csv(output, sep='\t', index=False, mode='w', lineterminator='\n')
                        output.write('\n')
                    elif i == 3:
                        output.write('#type' + '\t' + '\t' + '\t' + '\t' + '\t' + '\t' + '#token\n')
                        output.write(
                            'cl_phr_big_chunk' + '\t' + '\t' + '\t' + '\t' + '\t' + '\t' + 'cl_phr_big_chunk\n')
                        construct_csvs[i].to_csv(output, sep='\t', index=False, mode='w', lineterminator='\n')
                        output.write('\n')
                        r2_csvs[i].to_csv(output, sep='\t', index=False, mode='w', lineterminator='\n')
                        output.write('\n')
                    elif i == 4:
                        output.write('#type' + '\t' + '\t' + '\t' + '\t' + '\t' + '\t' + '#token'
                                     + '\t' + '\t' + '\t' + '\t' + '\t' + '\t' +
                                     '#type' + '\t' + '\t' + '\t' + '\t' + '\t' + '\t' + '#token\n')
                        output.write(
                            'phr_big_chunk_chunk' + '\t' + '\t' + '\t' + '\t' + '\t' + '\t' + 'phr_big_chunk_chunk'
                            + '\t' + '\t' + '\t' + '\t' + '\t' + '\t' +
                            'phr_big_chunk_chunk2' + '\t' + '\t' + '\t' + '\t' + '\t' + '\t' + 'phr_big_chunk_chunk2\n'
                        )
                        construct_csvs[i].to_csv(output, sep='\t', index=False, mode='w', lineterminator='\n')
                        output.write('\n')
                        r2_csvs[i].to_csv(output, sep='\t', index=False, mode='w', lineterminator='\n')
                        output.write('\n')
                    elif i == 5:
                        output.write('#type' + '\t' + '\t' + '\t' + '\t' + '\t' + '\t' + '#token'
                                     + '\t' + '\t' + '\t' + '\t' + '\t' + '\t' +
                                     '#type' + '\t' + '\t' + '\t' + '\t' + '\t' + '\t' + '#token\n')
                        output.write(
                            'big_chunk_chunk_w' + '\t' + '\t' + '\t' + '\t' + '\t' + '\t' + 'big_chunk_chunk_w'
                                     + '\t' + '\t' + '\t' + '\t' + '\t' + '\t' +
                                     'big_chunk_chunk_w2' + '\t' + '\t' + '\t' + '\t' + '\t' + '\t' + 'big_chunk_chunk_w2\n'
                                     )
                        construct_csvs[i].to_csv(output, sep='\t', index=False, mode='w', lineterminator='\n')
                        output.write('\n')
                        r2_csvs[i].to_csv(output, sep='\t', index=False, mode='w', lineterminator='\n')
                        output.write('\n')
                    elif i == 6:
                        output.write('#type' + '\t' + '\t' + '\t' + '\t' + '\t' + '\t' + '#token'
                                     + '\t' + '\t' + '\t' + '\t' + '\t' + '\t' +
                                     '#type' + '\t' + '\t' + '\t' + '\t' + '\t' + '\t' + '#token\n')
                        output.write('chunk_word_syl' + '\t' + '\t' + '\t' + '\t' + '\t' + '\t' + 'chunk_word_syl'
                                     + '\t' + '\t' + '\t' + '\t' + '\t' + '\t' +
                                     'chunk_word_syl2' + '\t' + '\t' + '\t' + '\t' + '\t' + '\t' + 'chunk_word_syl2\n'
                                     )
                        construct_csvs[i].to_csv(output, sep='\t', index=False, mode='w', lineterminator='\n')
                        output.write('\n')
                        r2_csvs[i].to_csv(output, sep='\t', index=False, mode='w', lineterminator='\n')
                        output.write('\n')
                    elif i == 7:
                        output.write('#type' + '\t' + '\t' + '\t' + '\t' + '\t' + '\t' + '#token\n')
                        output.write('word_syl_char' + '\t' + '\t' + '\t' + '\t' + '\t' + '\t' + 'word_syl_char\n')
                        construct_csvs[i].to_csv(output, sep='\t', index=False, mode='w', lineterminator='\n')
                        output.write('\n')
                        r2_csvs[i].to_csv(output, sep='\t', index=False, mode='w', lineterminator='\n')
                        output.write('\n')