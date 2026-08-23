import os
import csv
from collections import defaultdict
import SUD_parser_main_clause
from statistics import mean

"""The length vs position with 0.1% merging. All leftover positions are merged to the last possible one.
Includes expanded hierarchy: Sentences -> Main Clauses -> Clauses -> Phrases -> Subphrases -> Chunks -> Words."""

# --- CONFIGURATION ---
main_directory = 'C:/Users/nogol/Documents/Doktorat/corpora240717/SUD/processed/260403_saved/'
path_all = 'C:/Users/nogol/Documents/Doktorat/Analyzy/SUD/vysledky260403/Characteristics/length_vs_position/sort_by_mean_id'


# --- UTILITY FUNCTIONS ---

def get_weight_avg_limit(a_treebank):
    """Calculates the 0.1% threshold for different unit types based on unique forms."""
    type_sentences = []
    type_main_clauses = []
    type_clauses = []
    type_phrases = []
    type_big_chunk = []
    type_chunk = []

    for sentence in a_treebank.sentence_list:
        if sentence.root_good and not sentence.bad_things and sentence.num_conj <= 1:
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
                                type_chunk.append(chunk.word_form)

    return (len(set(type_sentences)) / 1000,
            len(set(type_main_clauses)) / 1000,
            len(set(type_clauses)) / 1000,
            len(set(type_phrases)) / 1000,
            len(set(type_big_chunk)) / 1000,
            len(set(type_chunk)) / 1000)


def merge_outliers(data_dict, constant):
    """Merges categories with N < constant, tracking weighted parent sizes and folding extra positions."""
    if not data_dict:
        return {}

    sorted_keys = sorted(data_dict.keys(), reverse=True)

    for num_units in sorted_keys:
        current_n = len(data_dict[num_units][0]['words']) if 0 in data_dict[num_units] else 0

        if current_n < constant and len(data_dict) > 1:
            remaining_keys = sorted([k for k in data_dict.keys() if k < num_units])
            if not remaining_keys:
                target_key = min([k for k in data_dict.keys() if k > num_units])
            else:
                target_key = max(remaining_keys)

            # 1. Merge the parent size tracking list
            data_dict[target_key]['parent_sizes'].extend(data_dict[num_units]['parent_sizes'])

            # 2. Merge data for positions
            last_pos_target = target_key - 1

            for pos in range(num_units):
                if pos < last_pos_target:
                    data_dict[target_key][pos]['words'].extend(data_dict[num_units][pos]['words'])
                    if 'subunits' in data_dict[num_units][pos]:
                        data_dict[target_key][pos]['subunits'].extend(data_dict[num_units][pos]['subunits'])
                else:
                    # Tail-Folding logic
                    data_dict[target_key][last_pos_target]['words'].extend(data_dict[num_units][pos]['words'])
                    if 'subunits' in data_dict[num_units][pos]:
                        data_dict[target_key][last_pos_target]['subunits'].extend(data_dict[num_units][pos]['subunits'])

            del data_dict[num_units]

    return data_dict


def export_to_csv(data_dict, file_path, mode='words', metric_label="Avg Words"):
    """Writes weighted parent sizes and position averages to CSV files."""
    if not data_dict: return

    sample_key = next(iter(data_dict))
    if mode == 'subunits' and 'subunits' not in data_dict[sample_key][0]: return

    max_pos = max(data_dict.keys())

    with open(file_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        headers = ['Weighted Parent Size', 'Count (N)'] + [f'Pos {i + 1} - {metric_label}' for i in range(max_pos)]
        writer.writerow(headers)

        for key in sorted(data_dict.keys()):
            p_sizes = data_dict[key]['parent_sizes']
            weighted_parent_val = round(sum(p_sizes) / len(p_sizes), 4)
            unit_count = len(p_sizes)
            row = [weighted_parent_val, unit_count]

            for pos in range(key):
                vals = data_dict[key][pos][mode]
                row.append(round(sum(vals) / len(vals), 4) if vals else 0)
            writer.writerow(row)


# --- MAIN ANALYSIS ---

def characteristics_units(a_treebank, output_folder, file_name):
    print(f'Extracting: {file_name}')
    w_sentence, w_main_clause, w_clause, w_phrase, w_big_chunk, w_chunk = get_weight_avg_limit(a_treebank)

    def factory():
        d = defaultdict(lambda: {'words': [], 'subunits': []})
        d['parent_sizes'] = []
        return d

    sentence_data = defaultdict(factory)
    main_clause_data = defaultdict(factory)
    phrase_data = defaultdict(factory)
    subphrase_data = defaultdict(factory)
    chunk_data = defaultdict(factory)
    chunk2_data = defaultdict(factory)
    chunk_word_data = defaultdict(factory)
    chunk2_word_data = defaultdict(factory)

    for sentence in a_treebank.sentence_list:
        if sentence.root_good and not sentence.bad_things and sentence.num_conj <= 1:

            # --- 1. SENTENCE LEVEL ---
            v_main_clauses = [mc for mc in sentence.main_clause_list if len(mc.word_list) > 0]
            if v_main_clauses:
                #sorted_mc = sorted(v_main_clauses, key=lambda mc: min([w.id for w in mc.word_list]))
                sorted_mc = sorted(v_main_clauses, key=lambda mc: mean([w.id for w in mc.word_list]))
                n_s = len(sorted_mc)
                sentence_data[n_s]['parent_sizes'].append(n_s)

                for s_i, mc in enumerate(sorted_mc):
                    sentence_data[n_s][s_i]['words'].append(len(mc.word_list))
                    sentence_data[n_s][s_i]['subunits'].append(len(mc.clause_list))

                    # --- 2. MAIN CLAUSE LEVEL ---
                    v_clauses = [cl for cl in mc.clause_list if len(cl.word_list) > 0]
                    if v_clauses:
                        #sorted_cl = sorted(v_clauses, key=lambda cl: min([w.id for w in cl.word_list]))
                        sorted_cl = sorted(v_clauses, key=lambda cl: mean([w.id for w in cl.word_list]))
                        n_mc = len(sorted_cl)
                        main_clause_data[n_mc]['parent_sizes'].append(n_mc)

                        for m_i, clause in enumerate(sorted_cl):
                            main_clause_data[n_mc][m_i]['words'].append(len(clause.word_list))
                            main_clause_data[n_mc][m_i]['subunits'].append(len(clause.phrase_list))

                            # --- 3. CLAUSE LEVEL (Phrases) ---
                            v_phrases = [p for p in clause.phrase_list if len(p.word_list) > 0]
                            if v_phrases:
                                #sorted_p = sorted(v_phrases, key=lambda p: p.root_phrase.id if p.root_phrase else min([w.id for w in p.word_list]))
                                #sorted_p = sorted(v_phrases, key=lambda p: min([w.id for w in p.word_list]))
                                sorted_p = sorted(v_phrases, key=lambda p: mean([w.id for w in p.word_list]))
                                n_cl = len(sorted_p)
                                phrase_data[n_cl]['parent_sizes'].append(n_cl)

                                for p_i, p in enumerate(sorted_p):
                                    phrase_data[n_cl][p_i]['words'].append(len(p.word_list))
                                    phrase_data[n_cl][p_i]['subunits'].append(len(p.big_chunk_list))

                                    # --- 4. PHRASE LEVEL (Subphrases) ---
                                    v_sub = [sp for sp in p.big_chunk_list if len(sp.word_list) > 0]
                                    if v_sub:
                                        #sorted_s = sorted(v_sub, key=lambda sp: sp.root_BigChunk.id if sp.root_BigChunk else min([w.id for w in sp.word_list]))
                                        #sorted_s = sorted(v_sub, key=lambda sp: min([w.id for w in sp.word_list]))
                                        sorted_s = sorted(v_sub, key=lambda sp: mean([w.id for w in sp.word_list]))
                                        ns = len(sorted_s)
                                        subphrase_data[ns]['parent_sizes'].append(ns)

                                        for sp_i, sp in enumerate(sorted_s):
                                            subphrase_data[ns][sp_i]['words'].append(len(sp.word_list))
                                            subphrase_data[ns][sp_i]['subunits'].append(len(sp.chunk_list))

                                            # --- 5 & 6. CHUNKS AND WORDS ---
                                            for c_list, d_target, d_word_target in [
                                                (sp.chunk_list, chunk_data, chunk_word_data),
                                                (sp.chunk2_list, chunk2_data, chunk2_word_data)]:
                                                v_ch = [ch for ch in c_list if len(ch.word_list) > 0]
                                                if v_ch:
                                                    #sorted_ch = sorted(v_ch,key=lambda ch: min([w.id for w in ch.word_list]))
                                                    sorted_ch = sorted(v_ch,key=lambda ch: mean([w.id for w in ch.word_list]))
                                                    nc = len(sorted_ch)
                                                    d_target[nc]['parent_sizes'].append(nc)

                                                    for c_i, ch in enumerate(sorted_ch):
                                                        d_target[nc][c_i]['words'].append(len(ch.word_list))

                                                        # Words within chunks (measuring syllables)
                                                        v_words = [w for w in ch.word_list]
                                                        if v_words:
                                                            sorted_w = sorted(v_words, key=lambda w: w.id)
                                                            nw = len(sorted_w)
                                                            d_word_target[nw]['parent_sizes'].append(nw)

                                                            for w_i, word in enumerate(sorted_w):
                                                                syllabs = word.num_syllab if getattr(word, 'num_syllab',
                                                                                                     None) is not None else 0
                                                                d_word_target[nw][w_i]['words'].append(syllabs)

    # Apply Merging with Tail-Folding
    sentence_data = merge_outliers(sentence_data, w_sentence)
    main_clause_data = merge_outliers(main_clause_data, w_main_clause)
    phrase_data = merge_outliers(phrase_data, w_clause)
    subphrase_data = merge_outliers(subphrase_data, w_phrase)
    chunk_data = merge_outliers(chunk_data, w_big_chunk)
    chunk2_data = merge_outliers(chunk2_data, w_big_chunk)
    chunk_word_data = merge_outliers(chunk_word_data, w_chunk)
    chunk2_word_data = merge_outliers(chunk2_word_data, w_chunk)

    if not os.path.exists(output_folder): os.makedirs(output_folder)

    # Export Sentences
    export_to_csv(sentence_data, os.path.join(output_folder, f'{file_name}_sentences_words.csv'), 'words', "Avg Words")
    export_to_csv(sentence_data, os.path.join(output_folder, f'{file_name}_sentences_clauses.csv'), 'subunits',
                  "Avg Clauses")

    # Export Main Clauses
    export_to_csv(main_clause_data, os.path.join(output_folder, f'{file_name}_main_clauses_words.csv'), 'words',
                  "Avg Words")
    export_to_csv(main_clause_data, os.path.join(output_folder, f'{file_name}_main_clauses_phrases.csv'), 'subunits',
                  "Avg Phrases")

    # Export Clauses (Phrases)
    export_to_csv(phrase_data, os.path.join(output_folder, f'{file_name}_phrases_words.csv'), 'words', "Avg Words")
    export_to_csv(phrase_data, os.path.join(output_folder, f'{file_name}_phrases_subunits.csv'), 'subunits',
                  "Avg Subphrases")

    # Export Phrases (Subphrases)
    export_to_csv(subphrase_data, os.path.join(output_folder, f'{file_name}_subphrases_words.csv'), 'words',
                  "Avg Words")
    export_to_csv(subphrase_data, os.path.join(output_folder, f'{file_name}_subphrases_subunits.csv'), 'subunits',
                  "Avg Chunks")

    # Export Chunks
    export_to_csv(chunk_data, os.path.join(output_folder, f'{file_name}_chunks_words.csv'), 'words', "Avg Words")
    export_to_csv(chunk2_data, os.path.join(output_folder, f'{file_name}_chunks2_words.csv'), 'words', "Avg Words")

    # Export Words inside Chunks (Syllables)
    export_to_csv(chunk_word_data, os.path.join(output_folder, f'{file_name}_chunk_words_syllables.csv'), 'words',
                  "Avg Syllables")
    export_to_csv(chunk2_word_data, os.path.join(output_folder, f'{file_name}_chunk2_words_syllables.csv'), 'words',
                  "Avg Syllables")


if __name__ == "__main__":
    pickle_list = [f for f in os.listdir(main_directory) if f.endswith('.pkl')]
    for p_file in pickle_list:
        name = p_file.replace('.pkl', '')
        treebank = SUD_parser_main_clause.load_treebank_pkl(os.path.join(main_directory, p_file))
        characteristics_units(treebank, path_all, name)
    print("Done!")