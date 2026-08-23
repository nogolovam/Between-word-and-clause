import os
import csv
import math
from collections import defaultdict, Counter
import SUD_parser_main_clause
from statistics import mean

"""
Modified Script: Deprel Sequences & Distributions vs Position with 0.1% merging.
Leftover positions are merged to the last possible one (tail-folding).
1. Calculates normalized unique deprel sequences per position.
2. Calculates the RAW COUNT of unique combinations (types) per position (Separate Table).
3. Calculates Shannon Entropy of the combinations per position (Separate Table).
"""

# --- CONFIGURATION ---
main_directory = 'C:/Users/nogol/Documents/Doktorat/corpora240717/SUD/processed/260403_saved/'
path_all = 'C:/Users/nogol/Documents/Doktorat/Analyzy/SUD/vysledky260403/Characteristics/entropy_deprel_sentence/'


# --- UTILITY FUNCTIONS ---

def get_weight_avg_limit(a_treebank):
    """Calculates the 0.1% threshold for different unit types based on unique forms."""
    type_sentences, type_main_clauses, type_clauses = [], [], []
    type_phrases, type_big_chunk, type_chunk = [], [], []

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

    return (len(set(type_sentences)) / 100,
            len(set(type_main_clauses)) / 100,
            len(set(type_clauses)) / 100,
            len(set(type_phrases)) / 100,
            len(set(type_big_chunk)) / 100,
            len(set(type_chunk)) / 100)


def merge_outliers(data_dict, constant):
    """Merges categories with N < constant, applying tail-folding to the deprel sequences."""
    if not data_dict:
        return {}

    sorted_keys = sorted(data_dict.keys(), reverse=True)

    for num_units in sorted_keys:
        current_n = len(data_dict[num_units][0]['deprel_sets']) if 0 in data_dict[num_units] else 0

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
                    # Direct position merge
                    data_dict[target_key][pos]['deprel_sets'].extend(data_dict[num_units][pos]['deprel_sets'])
                else:
                    # Tail-Folding logic
                    data_dict[target_key][last_pos_target]['deprel_sets'].extend(
                        data_dict[num_units][pos]['deprel_sets'])

            del data_dict[num_units]

    return data_dict


def export_normalized_sets(data_dict, file_path):
    """Writes the normalized unique deprel sequences per position to a CSV."""
    if not data_dict: return
    max_pos = max(data_dict.keys())

    # Calculate the total number of units of this level across the entire treebank/dataset
    total_corpus_units = sum(len(data_dict[key][pos]['deprel_sets']) for key in data_dict for pos in range(key))

    with open(file_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        headers = ['Weighted Parent Size', 'Count (N)'] + [f'Pos {i + 1} - Normalized Unique Sequences' for i in
                                                           range(max_pos)]
        writer.writerow(headers)

        for key in sorted(data_dict.keys()):
            p_sizes = data_dict[key]['parent_sizes']
            weighted_parent_val = round(sum(p_sizes) / len(p_sizes), 4)
            unit_count = len(p_sizes)
            row = [weighted_parent_val, unit_count]

            for pos in range(key):
                sets_at_pos = data_dict[key][pos]['deprel_sets']

                if total_corpus_units > 0 and len(sets_at_pos) > 0:
                    unique_sets = len(set(sets_at_pos))
                    # Normalize by the grand total of all instances of this unit
                    normalized_score = (unique_sets / total_corpus_units) * 1000
                    row.append(round(normalized_score, 4))
                else:
                    row.append(0)

            writer.writerow(row)


def export_unique_types(data_dict, file_path):
    """
    Calculates only the Raw Count of Unique Types per position and writes to a separate file.
    """
    if not data_dict: return
    max_pos = max(data_dict.keys())

    with open(file_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        headers = ['Total Units in Parent (x)', 'Count (N)'] + [f'Pos {i + 1} Unique Types' for i in range(max_pos)]
        writer.writerow(headers)

        for key in sorted(data_dict.keys()):
            p_sizes = data_dict[key]['parent_sizes']
            unit_count = len(p_sizes)
            row = [key, unit_count]

            for pos in range(key):
                sets_at_pos = data_dict[key][pos]['deprel_sets']
                if len(sets_at_pos) == 0:
                    row.append(0)
                    continue

                # Count unique types
                unique_type_count = len(set(sets_at_pos))
                row.append(unique_type_count)

            writer.writerow(row)


def export_entropy(data_dict, file_path):
    """
    Calculates only the Shannon Entropy per position and writes to a separate file.
    """
    if not data_dict: return
    max_pos = max(data_dict.keys())

    with open(file_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        headers = ['Total Units in Parent (x)', 'Count (N)'] + [f'Pos {i + 1} Entropy (bits)' for i in range(max_pos)]
        writer.writerow(headers)

        for key in sorted(data_dict.keys()):
            p_sizes = data_dict[key]['parent_sizes']
            unit_count = len(p_sizes)
            row = [key, unit_count]

            for pos in range(key):
                sets_at_pos = data_dict[key][pos]['deprel_sets']
                total_tokens_at_pos = len(sets_at_pos)

                if total_tokens_at_pos == 0:
                    row.append(0)
                    continue

                # Count frequencies for entropy
                set_counts = Counter(sets_at_pos)

                # Calculate Shannon Entropy
                entropy = 0.0
                for count in set_counts.values():
                    probability = count / total_tokens_at_pos
                    if probability > 0:
                        entropy -= probability * math.log2(probability)

                row.append(round(entropy, 4))

            writer.writerow(row)

def export_relative_entropy(data_dict, file_path):
    if not data_dict: return
    max_pos = max(data_dict.keys())
    with open(file_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        headers = ['Weighted Avg Units (x)', 'Count (N)'] + [f'Pos {i + 1} Relative Entropy' for i in
                                                             range(max_pos)]
        writer.writerow(headers)

        for key in sorted(data_dict.keys()):
            p_sizes = data_dict[key]['parent_sizes']
            weighted_len = sum(p_sizes) / len(p_sizes)
            row = [round(weighted_len, 2), len(p_sizes)]
            for pos in range(key):
                sets = data_dict[key][pos]['deprel_sets']
                total = len(sets)
                if total == 0:
                    row.append(0);
                    continue

                counts = Counter(sets)
                num_types = len(counts)

                # Calculate Shannon Entropy first to derive Relative Entropy
                entropy = sum(-(count / total) * math.log2(count / total) for count in counts.values())

                # Relative Entropy = H / log2(n)
                max_entropy = math.log2(num_types) if num_types > 1 else 1.0
                rel_entropy = entropy / max_entropy if max_entropy > 0 else 0

                row.append(round(rel_entropy, 4))
            writer.writerow(row)


# --- MAIN ANALYSIS ---

def process_unit(unit, data_dict, total_units_in_parent, pos):
    """Helper to extract exact sequences of deprels and update data dicts."""
    deprels = [getattr(w, 'deprel', 'UNK').split('@')[0] for w in unit.word_list]

    if deprels:
        # Keeps the exact original sequence of deprels as they appear in the unit
        deprel_set_string = "+".join(deprels)
        data_dict[total_units_in_parent][pos]['deprel_sets'].append(deprel_set_string)


def characteristics_units(a_treebank, output_folder, file_name):
    print(f'Extracting: {file_name}')
    w_sentence, w_main_clause, w_clause, w_phrase, w_big_chunk, w_chunk = get_weight_avg_limit(a_treebank)

    def factory():
        d = defaultdict(lambda: {'deprel_sets': []})
        d['parent_sizes'] = []
        return d

    sentence_data = defaultdict(factory)
    main_clause_data = defaultdict(factory)
    phrase_data = defaultdict(factory)
    subphrase_data = defaultdict(factory)
    chunk_data = defaultdict(factory)
    chunk2_data = defaultdict(factory)

    for sentence in a_treebank.sentence_list:
        if sentence.root_good and not sentence.bad_things and sentence.num_conj <= 1:

            all_main_clauses, all_clauses, all_phrases = [], [], []
            all_subphrases, all_chunks, all_chunk2s = [], [], []

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

            # --- PROCESS LEVELS ---

            if all_main_clauses:
                sorted_mc = sorted(all_main_clauses, key=lambda u: mean([w.id for w in u.word_list]))
                n_mc = len(sorted_mc)
                sentence_data[n_mc]['parent_sizes'].append(n_mc)
                for pos, mc in enumerate(sorted_mc):
                    process_unit(mc, sentence_data, n_mc, pos)

            if all_clauses:
                sorted_cl = sorted(all_clauses, key=lambda u: mean([w.id for w in u.word_list]))
                n_cl = len(sorted_cl)
                main_clause_data[n_cl]['parent_sizes'].append(n_cl)
                for pos, cl in enumerate(sorted_cl):
                    process_unit(cl, main_clause_data, n_cl, pos)

            if all_phrases:
                sorted_ph = sorted(all_phrases, key=lambda u: mean([w.id for w in u.word_list]))
                n_ph = len(sorted_ph)
                phrase_data[n_ph]['parent_sizes'].append(n_ph)
                for pos, p in enumerate(sorted_ph):
                    process_unit(p, phrase_data, n_ph, pos)

            if all_subphrases:
                sorted_sp = sorted(all_subphrases, key=lambda u: mean([w.id for w in u.word_list]))
                n_sp = len(sorted_sp)
                subphrase_data[n_sp]['parent_sizes'].append(n_sp)
                for pos, sp in enumerate(sorted_sp):
                    process_unit(sp, subphrase_data, n_sp, pos)

            if all_chunks:
                sorted_ch = sorted(all_chunks, key=lambda u: mean([w.id for w in u.word_list]))
                n_ch = len(sorted_ch)
                chunk_data[n_ch]['parent_sizes'].append(n_ch)
                for pos, ch in enumerate(sorted_ch):
                    process_unit(ch, chunk_data, n_ch, pos)

            if all_chunk2s:
                sorted_ch2 = sorted(all_chunk2s, key=lambda u: mean([w.id for w in u.word_list]))
                n_ch2 = len(sorted_ch2)
                chunk2_data[n_ch2]['parent_sizes'].append(n_ch2)
                for pos, ch2 in enumerate(sorted_ch2):
                    process_unit(ch2, chunk2_data, n_ch2, pos)

    if not os.path.exists(output_folder): os.makedirs(output_folder)

    # --- APPLY MERGING ---
    # Apply 0.1% threshold and tail-folding logic
    sentence_data = merge_outliers(sentence_data, w_sentence)
    main_clause_data = merge_outliers(main_clause_data, w_main_clause)
    phrase_data = merge_outliers(phrase_data, w_phrase)
    subphrase_data = merge_outliers(subphrase_data, w_big_chunk)
    chunk_data = merge_outliers(chunk_data, w_chunk)

    # --- EXPORT 1: UNIQUE TYPES ---
    #export_unique_types(sentence_data, os.path.join(output_folder, f'{file_name}_mc_merged_unique_types.csv'))
    #export_unique_types(main_clause_data, os.path.join(output_folder, f'{file_name}_clauses_merged_unique_types.csv'))
    #export_unique_types(phrase_data, os.path.join(output_folder, f'{file_name}_phrases_merged_unique_types.csv'))
    #export_unique_types(subphrase_data, os.path.join(output_folder, f'{file_name}_subphrases_merged_unique_types.csv'))
    #export_unique_types(chunk_data, os.path.join(output_folder, f'{file_name}_chunks_merged_unique_types.csv'))

    # --- EXPORT 2: SHANNON ENTROPY ---
    #export_entropy(sentence_data, os.path.join(output_folder, f'{file_name}_mc_merged_entropy.csv'))
    #export_entropy(main_clause_data, os.path.join(output_folder, f'{file_name}_clauses_merged_entropy.csv'))
    #export_entropy(phrase_data, os.path.join(output_folder, f'{file_name}_phrases_merged_entropy.csv'))
    #export_entropy(subphrase_data, os.path.join(output_folder, f'{file_name}_subphrases_merged_entropy.csv'))
    #export_entropy(chunk_data, os.path.join(output_folder, f'{file_name}_chunks_merged_entropy.csv'))

    # Keep original normalized export for merged data
    #export_normalized_sets(sentence_data, os.path.join(output_folder, f'{file_name}_mc_merged_normalized_seq.csv'))
    #export_normalized_sets(main_clause_data,os.path.join(output_folder, f'{file_name}_clauses_merged_normalized_seq.csv'))
    export_normalized_sets(phrase_data, os.path.join('C:/Users/nogol/Documents/Doktorat/Analyzy/SUD/vysledky260403/Characteristics/for_plots/for_thesis/phrases/rel_counts/deprel_entropy_type', f'01{file_name}_phrases_merged_normalized_seq.csv'))
    export_normalized_sets(subphrase_data,os.path.join('C:/Users/nogol/Documents/Doktorat/Analyzy/SUD/vysledky260403/Characteristics/for_plots/for_thesis/subphrases/rel_counts/deprel_entropy_type', f'01{file_name}_subphrases_merged_normalized_seq.csv'))
    export_normalized_sets(chunk_data, os.path.join('C:/Users/nogol/Documents/Doktorat/Analyzy/SUD/vysledky260403/Characteristics/for_plots/for_thesis/chunk/rel_counts/deprel_entropy_type', f'01{file_name}_chunks_merged_normalized_seq.csv'))


    # --- EXPORT 3: Relative entropy ---
    #export_relative_entropy(phrase_data, os.path.join('C:/Users/nogol/Documents/Doktorat/Analyzy/SUD/vysledky260403/Characteristics/for_plots/for_thesis/phrases/deprel_entropy_type', f'07{file_name}_phrases_merged_rel_entropy_sen.csv'))
    #export_relative_entropy(subphrase_data, os.path.join('C:/Users/nogol/Documents/Doktorat/Analyzy/SUD/vysledky260403/Characteristics/for_plots/for_thesis/subphrases/deprel_entropy_type', f'07{file_name}_subphrases_merged_rel_entropy_sen.csv'))
    #export_relative_entropy(chunk_data, os.path.join('C:/Users/nogol/Documents/Doktorat/Analyzy/SUD/vysledky260403/Characteristics/for_plots/for_thesis/chunk/deprel_entropy_type', f'07{file_name}_chunks_merged_rel_entropy_sen.csv'))

if __name__ == "__main__":
    pickle_list = [f for f in os.listdir(main_directory) if f.endswith('.pkl')]
    for p_file in pickle_list:
        name = p_file.replace('.pkl', '')
        treebank = SUD_parser_main_clause.load_treebank_pkl(os.path.join(main_directory, p_file))
        characteristics_units(treebank, path_all, name)
    print("Done!")