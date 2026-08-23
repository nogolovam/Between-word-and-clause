"""Script was updated, new chunk (without reflecting linearity) was implemented, detection of clause was updated (coordination of predicate_in_SCONJ)"""

import os
import SUD_parser_main_clause
import Main_clause_MAL2 as S

# sentence - independent clause - clause - phrase - subphrase - chunk - word - syllab - char
#verze aktualní, po korekci klauzí
# použito naposledy 16. 4. 2026

main_directory = 'C:/Users/nogol/Documents/Doktorat/corpora240717/SUD/processed/260403_saved/'
main_directory_make_treebank = 'C:/Users/nogol/Documents/Doktorat/corpora240717/SUD/processed'

path_all = 'C:/Users/nogol/Documents/Doktorat/Analyzy/SUD/vysledky260403/MAL'

def make_treebank(file_directory):

    conllu_file_list = list(filter(lambda x: '.conllu' in x, os.listdir(file_directory)))

    for conllu_file in conllu_file_list:
        parts = conllu_file.split('/')
        name = parts[-1].split('.')[0]
        print("Making treebank from " + name)

        a_treebank = SUD_parser_main_clause.create_treebank(file_directory + '/' + conllu_file)
        SUD_parser_main_clause.save_treebank(a_treebank, file_directory + '/260403_saved/' + name + '.pkl')

#make_treebank(main_directory_make_treebank)


def export_info (file_directory, output_file_directory):
    kat = ['bez_conj1']

    pickle_list = list(filter(lambda x: '.pkl' in x, os.listdir(file_directory)))
    for pickle_file in pickle_list:
        parts = pickle_file.split('/')
        name = parts[-1].split('.')[0]
        print("Info: start with " + name)
        treebank = name

        a_treebank = SUD_parser_main_clause.load_treebank_pkl(file_directory + '/' + pickle_file)

        for k in kat:
            S.get_info(a_treebank, output_file_directory, k, treebank)

#export_info(main_directory, path_all)


def export_MAL(file_directory, path_all):
    kat = ['bez_conj1']

    pickle_list = list(filter(lambda x: '.pkl' in x, os.listdir(file_directory)))
    for pickle_file in pickle_list:
        parts = pickle_file.split('/')
        name = parts[-1].split('.')[0]
        print("MAL: start with " + name)
        treebank = name

        a_treebank = SUD_parser_main_clause.load_treebank_pkl(file_directory + '/' + pickle_file)

        for k in kat:
            S.get_info(a_treebank, path_all, k, treebank)
            cathegory = k
            file_path_s = f'{path_all}/{cathegory}/{treebank}/sen_maincl_cl/'

            if not os.path.exists(file_path_s):
                os.makedirs(file_path_s)

            file_path_mc = f'{path_all}/{cathegory}/{treebank}/maincl_cl_phr/'

            if not os.path.exists(file_path_mc):
                os.makedirs(file_path_mc)

            file_path_c = f'{path_all}/{cathegory}/{treebank}/cl_phr_big_chunk/'

            if not os.path.exists(file_path_c):
                os.makedirs(file_path_c)

            file_path_phrase = f'{path_all}/{cathegory}/{treebank}/phr_big_chunk_chunk/'

            if not os.path.exists(file_path_phrase):
                os.makedirs(file_path_phrase)

            file_path_phrase2 = f'{path_all}/{cathegory}/{treebank}/phr_big_chunk_chunk2/'

            if not os.path.exists(file_path_phrase2):
                os.makedirs(file_path_phrase2)

            file_path_big_chunk = f'{path_all}/{cathegory}/{treebank}/big_chunk_chunk_w/'

            if not os.path.exists(file_path_big_chunk):
                os.makedirs(file_path_big_chunk)

            file_path_big_chunk2 = f'{path_all}/{cathegory}/{treebank}/big_chunk_chunk_w2/'

            if not os.path.exists(file_path_big_chunk2):
                os.makedirs(file_path_big_chunk2)

            file_path_chunk = f'{path_all}/{cathegory}/{treebank}/chunk_word_syl/'

            if not os.path.exists(file_path_chunk):
                os.makedirs(file_path_chunk)

            file_path_chunk2 = f'{path_all}/{cathegory}/{treebank}/chunk_word_syl2/'

            if not os.path.exists(file_path_chunk2):
                os.makedirs(file_path_chunk2)

            file_path_word = f'{path_all}/{cathegory}/{treebank}/word_syl_char/'

            if not os.path.exists(file_path_word):
                os.makedirs(file_path_word)

            weighted_avg_limit_sentence = S.get_weight_avg_limit(a_treebank, k)[0]  # nastavení min. frekvence (1 %); zvlášt pro všechny úrovně, řídit se typy
            weighted_avg_limit_mainclause = S.get_weight_avg_limit(a_treebank, k)[1]
            weighted_avg_limit_clause = S.get_weight_avg_limit(a_treebank, k)[2]
            weighted_avg_limit_phrase = S.get_weight_avg_limit(a_treebank, k)[3]
            weighted_avg_limit_big_chunk = S.get_weight_avg_limit(a_treebank, k)[4]
            weighted_avg_limit_chunk = S.get_weight_avg_limit(a_treebank, k)[5]
            weighted_avg_limit_chunk2 = S.get_weight_avg_limit(a_treebank, k)[6]
            weighted_avg_limit_word = S.get_weight_avg_limit(a_treebank, k)[7]

            # SYNTACTIC LEVEL
            # sentence level
            S.sentence_mainclause_clause_cut(a_treebank, weighted_avg_limit_sentence, file_path_s, k)

            # main clause level
            S.mainclause_clause_phrase_cut(a_treebank, weighted_avg_limit_mainclause, file_path_mc, k)

            # clause level
            S.clause_phrase_big_chunk_cut(a_treebank, weighted_avg_limit_clause, file_path_c, k)

            # phrase level
            S.phrase_big_chunk_chunk_cut(a_treebank, weighted_avg_limit_phrase, file_path_phrase, k)
            S.phrase_big_chunk_chunk_cut2(a_treebank, weighted_avg_limit_phrase, file_path_phrase, k)

            # big_chunk level
            S.big_chunk_chunk_word_cut(a_treebank, weighted_avg_limit_big_chunk, file_path_big_chunk, k)
            S.big_chunk_chunk_word_cut2(a_treebank, weighted_avg_limit_big_chunk, file_path_big_chunk, k)

            #unit level
            S.chunk_word_syllable_cut(a_treebank, weighted_avg_limit_chunk, file_path_chunk, k)
            S.chunk_word_syllable_cut2(a_treebank, weighted_avg_limit_chunk2, file_path_chunk, k)


            # word level
            S.word_syllable_char_cut(a_treebank, weighted_avg_limit_word, file_path_word, k)

#export_MAL(main_directory, path_all)


def process_nlreg_data_MAL(filename_list, model):
    """loops via a list of files containing xfy values of a given triplet of language units,
       creates NLREG program files and output files with results for both (truncated and complete) models"""

    for filename in filename_list:
        # checks content of a file if it is not empty
        if len(S.load_xfy_file(filename)) > 1:
            S.run_nlreg_MAL(filename, model)

'''
pickle_list = list(filter(lambda x: '.pkl' in x, os.listdir(main_directory)))

kat = ['bez_conj1']

for pickle_file in pickle_list:
    parts = pickle_file.split('/')
    name = parts[-1].split('.')[0]
    print("NLREG MAL: start with " + name)
    treebank = name

    for k in kat:
        cathegory = k

        file_path_s = f'{path_all}/{cathegory}/{treebank}/sen_maincl_cl/'
        file_path_mc = f'{path_all}/{cathegory}/{treebank}/maincl_cl_phr/'
        file_path_c = f'{path_all}/{cathegory}/{treebank}/cl_phr_big_chunk/'
        file_path_phrase = f'{path_all}/{cathegory}/{treebank}/phr_big_chunk_chunk/'
        file_path_phrase2 = f'{path_all}/{cathegory}/{treebank}/phr_big_chunk_chunk2/'
        file_path_big_chunk = f'{path_all}/{cathegory}/{treebank}/big_chunk_chunk_w/'
        file_path_big_chunk2 = f'{path_all}/{cathegory}/{treebank}/big_chunk_chunk_w2/'
        file_path_chunk = f'{path_all}/{cathegory}/{treebank}/chunk_word_syl/'
        file_path_chunk2 = f'{path_all}/{cathegory}/{treebank}/chunk_word_syl2/'
        file_path_word = f'{path_all}/{cathegory}/{treebank}/word_syl_char/'

        filename_list = [
            file_path_s + 'sen_maincl_cl_cut_xfy.txt',
            file_path_s + 'sen_maincl_cl_cut_xfy_weighted.txt',
            file_path_s + 'sen_maincl_cl_cut_type_xfy.txt',
            file_path_s + 'sen_maincl_cl_cut_type_xfy_weighted.txt',
            file_path_mc + 'maincl_cl_phr_cut_xfy.txt',
            file_path_mc + 'maincl_cl_phr_cut_xfy_weighted.txt',
            file_path_mc + 'maincl_cl_phr_cut_type_xfy.txt',
            file_path_mc + 'maincl_cl_phr_cut_type_xfy_weighted.txt',
            file_path_c + 'cl_phr_big_chunk_cut_xfy.txt',
            file_path_c + 'cl_phr_big_chunk_cut_xfy_weighted.txt',
            file_path_c + 'cl_phr_big_chunk_cut_type_xfy.txt',
            file_path_c + 'cl_phr_big_chunk_cut_type_xfy_weighted.txt',
            file_path_phrase + 'phr_big_chunk_chunk_cut_xfy.txt',
            file_path_phrase + 'phr_big_chunk_chunk_cut_xfy_weighted.txt',
            file_path_phrase + 'phr_big_chunk_chunk_cut_type_xfy.txt',
            file_path_phrase + 'phr_big_chunk_chunk_cut_type_xfy_weighted.txt',
            file_path_phrase2 + 'phr_big_chunk_chunk2_cut_xfy.txt',
            file_path_phrase2 + 'phr_big_chunk_chunk2_cut_xfy_weighted.txt',
            file_path_phrase2 + 'phr_big_chunk_chunk2_cut_type_xfy.txt',
            file_path_phrase2 + 'phr_big_chunk_chunk2_cut_type_xfy_weighted.txt',
            file_path_big_chunk + 'big_chunk_chunk_w_cut_xfy.txt',
            file_path_big_chunk + 'big_chunk_chunk_w_cut_xfy_weighted.txt',
            file_path_big_chunk + 'big_chunk_chunk_w_cut_type_xfy.txt',
            file_path_big_chunk + 'big_chunk_chunk_w_cut_type_xfy_weighted.txt',
            file_path_big_chunk2 + 'big_chunk_chunk_w2_cut_xfy.txt',
            file_path_big_chunk2 + 'big_chunk_chunk_w2_cut_xfy_weighted.txt',
            file_path_big_chunk2 + 'big_chunk_chunk_w2_cut_type_xfy.txt',
            file_path_big_chunk2 + 'big_chunk_chunk_w2_cut_type_xfy_weighted.txt',
            file_path_chunk + 'chunk_word_syl_cut_xfy.txt',
            file_path_chunk + 'chunk_word_syl_cut_xfy_weighted.txt',
            file_path_chunk + 'chunk_word_syl_cut_type_xfy.txt',
            file_path_chunk + 'chunk_word_syl_cut_type_xfy_weighted.txt',
            file_path_chunk2 + 'chunk_word_syl2_cut_xfy.txt',
            file_path_chunk2 + 'chunk_word_syl2_cut_xfy_weighted.txt',
            file_path_chunk2 + 'chunk_word_syl2_cut_type_xfy.txt',
            file_path_chunk2 + 'chunk_word_syl2_cut_type_xfy_weighted.txt',
            file_path_word + 'word_syl_char_cut_xfy.txt',
            file_path_word + 'word_syl_char_cut_xfy_weighted.txt',
            file_path_word + 'word_syl_char_cut_type_xfy.txt',
            file_path_word + 'word_syl_char_cut_type_xfy_weighted.txt'
        ]

        source_dirs = [
            file_path_s,
            file_path_mc,
            file_path_c,
            file_path_phrase,
            file_path_phrase2,
            file_path_big_chunk,
            file_path_big_chunk2,
            file_path_chunk,
            file_path_chunk2,
            file_path_word
        ]

        destination_dir_truncated = f'{path_all}/NLREG/truncated/{cathegory}/{treebank}/'

        if not os.path.exists(destination_dir_truncated):
            os.makedirs(destination_dir_truncated)

        destination_dir_c = f'{path_all}/NLREG/c/{cathegory}/{treebank}/'

        if not os.path.exists(destination_dir_c):
            os.makedirs(destination_dir_c)

        process_nlreg_data_MAL(filename_list, 'truncated')
        process_nlreg_data_MAL(filename_list, 'c')

        S.copy_lst_files(source_dirs, destination_dir_truncated, treebank, 'truncated')
        S.copy_lst_files(source_dirs, destination_dir_c, treebank, 'c')

        output_folder_NLREG_MAL_truncated = f'{path_all}/NLREG/truncated/{cathegory}/{treebank}/'
        output_folder_NLREG_MAL_c = f'{path_all}/NLREG/c/{cathegory}/{treebank}/'

        result_df_truncated = S.process_lst_files_MAL(output_folder_NLREG_MAL_truncated, 'truncated',
                                                      output_csv=output_folder_NLREG_MAL_truncated)
        result_df_c = S.process_lst_files_MAL(output_folder_NLREG_MAL_c, 'c', output_csv=output_folder_NLREG_MAL_c)
¨'''
#lang_mat = ['all_SUD', 'Bible', 'CAC', 'FIC', 'Fic_T', 'NFC', 'NMG', 'no_CAC', 'PDT', 'Poetry', 'prez', 'Pud']

kat = ['bez_conj1']
lang_mat = ['all_SUD']

levels = [
    'sen_maincl_cl',
    'maincl_cl_phr',
    'cl_phr_big_chunk',
    'phr_big_chunk_chunk', 'phr_big_chunk_chunk2',
    'big_chunk_chunk_w', 'big_chunk_chunk_w2',
    'chunk_word_syl', 'chunk_word_syl2',
    'word_syl_char'
]

# Run for both normal and weighted
S.main(path_all, lang_mat, kat, levels, weighted=False)
S.main(path_all, lang_mat, kat, levels, weighted=True)
