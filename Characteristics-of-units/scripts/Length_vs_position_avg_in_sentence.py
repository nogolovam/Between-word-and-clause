import os
import csv
from collections import defaultdict
import SUD_parser_main_clause
from statistics import mean

"""The length vs position with 0.1% merging. All leftover positions are merged to the last possible one.
Includes expanded hierarchy: Sentences -> Main Clauses -> Clauses -> Phrases -> Subphrases -> Chunks -> Words.
Flattened logic: Units are sorted linearly across the entire sentence, grouped by total units in the sentence."""

# --- CONFIGURATION ---
main_directory = 'C:/Users/nogol/Documents/Doktorat/corpora240717/SUD/processed/260403_saved/'
path_all = 'C:/Users/nogol/Documents/Doktorat/Analyzy/SUD/vysledky260403/Characteristics/length_vs_position_in_sentence/sort_by_mean_id'


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

            # 1. GATHER ALL UNITS IN THE SENTENCE
            all_main_clauses = []
            all_clauses = []
            all_phrases = []
            all_subphrases = []
            all_chunks = []
            all_chunk2s = []

            for mc in sentence.main_clause_list:
                if len(mc.word_list) > 0:
                    all_main_clauses.append(mc)
                for clause in mc.clause_list:
                    if len(clause.word_list) > 0:
                        all_clauses.append(clause)
                    for phrase in clause.phrase_list:
                        if len(phrase.word_list) > 0:
                            all_phrases.append(phrase)
                        for bc in phrase.big_chunk_list:
                            if len(bc.word_list) > 0:
                                all_subphrases.append(bc)
                            for chunk in bc.chunk_list:
                                if len(chunk.word_list) > 0:
                                    all_chunks.append(chunk)
                            for chunk2 in bc.chunk2_list:
                                if len(chunk2.word_list) > 0:
                                    all_chunk2s.append(chunk2)

            # 2. PROCESS EACH LEVEL LINEARLY ACROSS THE SENTENCE

            # --- SENTENCE LEVEL (Main Clauses) ---
            if all_main_clauses:
                #sorted_mc = sorted(all_main_clauses, key=lambda u: min([w.id for w in u.word_list]))
                sorted_mc = sorted(all_main_clauses, key=lambda u: mean([w.id for w in u.word_list]))
                n_mc = len(sorted_mc)
                sentence_data[n_mc]['parent_sizes'].append(n_mc)
                for pos, mc in enumerate(sorted_mc):
                    sentence_data[n_mc][pos]['words'].append(len(mc.word_list))
                    sentence_data[n_mc][pos]['subunits'].append(len(mc.clause_list))

            # --- MAIN CLAUSE LEVEL (Clauses) ---
            if all_clauses:
                #sorted_cl = sorted(all_clauses, key=lambda u: min([w.id for w in u.word_list]))
                sorted_cl = sorted(all_clauses, key=lambda u: mean([w.id for w in u.word_list]))
                n_cl = len(sorted_cl)
                main_clause_data[n_cl]['parent_sizes'].append(n_cl)
                for pos, cl in enumerate(sorted_cl):
                    main_clause_data[n_cl][pos]['words'].append(len(cl.word_list))
                    main_clause_data[n_cl][pos]['subunits'].append(len(cl.phrase_list))

            # --- CLAUSE LEVEL (Phrases) ---
            if all_phrases:
                #sorted_ph = sorted(all_phrases, key=lambda u: min([w.id for w in u.word_list]))
                sorted_ph = sorted(all_phrases, key=lambda u: mean([w.id for w in u.word_list]))
                n_ph = len(sorted_ph)
                phrase_data[n_ph]['parent_sizes'].append(n_ph)
                for pos, p in enumerate(sorted_ph):
                    phrase_data[n_ph][pos]['words'].append(len(p.word_list))
                    phrase_data[n_ph][pos]['subunits'].append(len(p.big_chunk_list))

            # --- PHRASE LEVEL (Subphrases / Big Chunks) ---
            if all_subphrases:
                #sorted_sp = sorted(all_subphrases, key=lambda u: min([w.id for w in u.word_list]))
                sorted_sp = sorted(all_subphrases, key=lambda u: mean([w.id for w in u.word_list]))
                n_sp = len(sorted_sp)
                subphrase_data[n_sp]['parent_sizes'].append(n_sp)
                for pos, sp in enumerate(sorted_sp):
                    subphrase_data[n_sp][pos]['words'].append(len(sp.word_list))
                    subphrase_data[n_sp][pos]['subunits'].append(len(sp.chunk_list))

            # --- CHUNKS LEVEL ---
            if all_chunks:
                #sorted_ch = sorted(all_chunks, key=lambda u: min([w.id for w in u.word_list]))
                sorted_ch = sorted(all_chunks, key=lambda u: mean([w.id for w in u.word_list]))
                n_ch = len(sorted_ch)
                chunk_data[n_ch]['parent_sizes'].append(n_ch)
                for pos, ch in enumerate(sorted_ch):
                    chunk_data[n_ch][pos]['words'].append(len(ch.word_list))

            # --- CHUNK2S LEVEL ---
            if all_chunk2s:
                #sorted_ch2 = sorted(all_chunk2s, key=lambda u: min([w.id for w in u.word_list]))
                sorted_ch2 = sorted(all_chunk2s, key=lambda u: mean([w.id for w in u.word_list]))
                n_ch2 = len(sorted_ch2)
                chunk2_data[n_ch2]['parent_sizes'].append(n_ch2)
                for pos, ch2 in enumerate(sorted_ch2):
                    chunk2_data[n_ch2][pos]['words'].append(len(ch2.word_list))

            # --- WORDS IN CHUNKS LEVEL (Syllables) ---
            all_chunk_words = []
            seen_cw = set()
            for ch in all_chunks:
                for w in ch.word_list:
                    if w.id not in seen_cw:
                        all_chunk_words.append(w)
                        seen_cw.add(w.id)

            if all_chunk_words:
                sorted_cw = sorted(all_chunk_words, key=lambda w: w.id)
                n_cw = len(sorted_cw)
                chunk_word_data[n_cw]['parent_sizes'].append(n_cw)
                for pos, w in enumerate(sorted_cw):
                    syllabs = w.num_syllab if getattr(w, 'num_syllab', None) is not None else 0
                    chunk_word_data[n_cw][pos]['words'].append(syllabs)

            # --- WORDS IN CHUNK2S LEVEL (Syllables) ---
            all_chunk2_words = []
            seen_cw2 = set()
            for ch2 in all_chunk2s:
                for w in ch2.word_list:
                    if w.id not in seen_cw2:
                        all_chunk2_words.append(w)
                        seen_cw2.add(w.id)

            if all_chunk2_words:
                sorted_cw2 = sorted(all_chunk2_words, key=lambda w: w.id)
                n_cw2 = len(sorted_cw2)
                chunk2_word_data[n_cw2]['parent_sizes'].append(n_cw2)
                for pos, w in enumerate(sorted_cw2):
                    syllabs = w.num_syllab if getattr(w, 'num_syllab', None) is not None else 0
                    chunk2_word_data[n_cw2][pos]['words'].append(syllabs)

    # Apply Merging with Tail-Folding
    sentence_data = merge_outliers(sentence_data, w_sentence)
    main_clause_data = merge_outliers(main_clause_data, w_main_clause)
    phrase_data = merge_outliers(phrase_data, w_phrase)
    subphrase_data = merge_outliers(subphrase_data, w_big_chunk)
    chunk_data = merge_outliers(chunk_data, w_chunk)
    chunk2_data = merge_outliers(chunk2_data, w_chunk)
    chunk_word_data = merge_outliers(chunk_word_data, w_chunk)
    chunk2_word_data = merge_outliers(chunk2_word_data, w_chunk)

    if not os.path.exists(output_folder): os.makedirs(output_folder)

    # Export Sentences
    export_to_csv(sentence_data, os.path.join(output_folder, f'{file_name}_mc_words.csv'), 'words', "Avg Words")
    export_to_csv(sentence_data, os.path.join(output_folder, f'{file_name}_mc_clauses.csv'), 'subunits',
                  "Avg Clauses")

    # Export Main Clauses
    export_to_csv(main_clause_data, os.path.join(output_folder, f'{file_name}_clauses_words.csv'), 'words',
                  "Avg Words")
    export_to_csv(main_clause_data, os.path.join(output_folder, f'{file_name}_clauses_phrases.csv'), 'subunits',
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