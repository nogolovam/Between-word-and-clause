import os
import csv
import statistics
from collections import defaultdict
import SUD_parser_main_clause

"""The embedding distance vs position with 0.1% merging. 
Calculates the Mean, Median, and Max of word.h_distance for units at various hierarchy levels.
Flattened logic: Units are sorted linearly across the entire sentence, grouped by total units in the clause.
Stops at the Chunk level."""

# --- CONFIGURATION ---
main_directory = 'C:/Users/nogol/Documents/Doktorat/corpora240717/SUD/pro_h_distance_clause/saved/'
path_all = 'C:/Users/nogol/Documents/Doktorat/Analyzy/SUD/vysledky260403/Characteristics/h_distance_vs_position_in_clause/sort_by_mean_id'


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

def get_h_distance_metrics(word_list):
    """Helper to calculate Mean, Median, and Max of h_distance for a list of words."""
    dists = [w.h_distance for w in word_list if getattr(w, 'h_distance_cl', None) is not None]
    if not dists:
        return 0.0, 0.0, 0.0
    return sum(dists) / len(dists), statistics.median(dists), max(dists)

def merge_outliers(data_dict, constant):
    """Merges categories with N < constant, tracking weighted parent sizes and folding extra positions."""
    if not data_dict:
        return {}

    sorted_keys = sorted(data_dict.keys(), reverse=True)

    for num_units in sorted_keys:
        # Check current N based on the h_dist_avg list length (representing unit count)
        current_n = len(data_dict[num_units][0]['h_dist_avg']) if 0 in data_dict[num_units] else 0

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
                    data_dict[target_key][pos]['h_dist_avg'].extend(data_dict[num_units][pos]['h_dist_avg'])
                    data_dict[target_key][pos]['h_dist_med'].extend(data_dict[num_units][pos]['h_dist_med'])
                    data_dict[target_key][pos]['h_dist_max'].extend(data_dict[num_units][pos]['h_dist_max'])
                else:
                    # Tail-Folding logic
                    data_dict[target_key][last_pos_target]['h_dist_avg'].extend(data_dict[num_units][pos]['h_dist_avg'])
                    data_dict[target_key][last_pos_target]['h_dist_med'].extend(data_dict[num_units][pos]['h_dist_med'])
                    data_dict[target_key][last_pos_target]['h_dist_max'].extend(data_dict[num_units][pos]['h_dist_max'])

            del data_dict[num_units]

    return data_dict


def export_to_csv(data_dict, file_path, mode='h_dist_avg', metric_label="Avg h_dist"):
    """Writes weighted parent sizes and position averages to CSV files."""
    if not data_dict: return

    sample_key = next(iter(data_dict))
    if mode not in data_dict[sample_key][0]: return

    max_pos = max(data_dict.keys())

    with open(file_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        headers = ['Weighted Parent Size', 'Count (N)'] + [f'Pos {i + 1} - {metric_label}' for i in range(max_pos)]
        writer.writerow(headers)

        for key in sorted(data_dict.keys()):
            p_sizes = data_dict[key]['parent_sizes']
            weighted_parent_val = round(sum(p_sizes) / len(p_sizes), 4) if p_sizes else 0
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
        d = defaultdict(lambda: {'h_dist_avg': [], 'h_dist_med': [], 'h_dist_max': []})
        d['parent_sizes'] = []
        return d

    #main_clause_data = defaultdict(factory)
    #clause_data = defaultdict(factory)
    phrase_data = defaultdict(factory)
    subphrase_data = defaultdict(factory)
    chunk_data = defaultdict(factory)

    for sentence in a_treebank.sentence_list:
        if sentence.root_good and not sentence.bad_things and sentence.num_conj <= 1:

            # 1. GATHER ALL UNITS IN THE SENTENCE
            #all_main_clauses = []
            #all_clauses = []


            for mc in sentence.main_clause_list:
                for clause in mc.clause_list:
                    all_phrases = []
                    all_subphrases = []
                    all_chunks = []
                    for phrase in clause.phrase_list:
                        if len(phrase.word_list) > 0:
                            all_phrases.append(phrase)
                        for bc in phrase.big_chunk_list:
                            if len(bc.word_list) > 0:
                                all_subphrases.append(bc)
                            for chunk in bc.chunk_list:
                                if len(chunk.word_list) > 0:
                                    all_chunks.append(chunk)

            # 2. PROCESS EACH LEVEL LINEARLY ACROSS THE SENTENCE


            # --- PHRASES ---
                    if all_phrases:
                        #sorted_ph = sorted(all_phrases, key=lambda u: min([w.id for w in u.word_list]))
                        sorted_ph = sorted(all_phrases, key=lambda u: statistics.mean([w.id for w in u.word_list]))
                        n_ph = len(sorted_ph)
                        phrase_data[n_ph]['parent_sizes'].append(n_ph)
                        for pos, unit in enumerate(sorted_ph):
                            avg_v, med_v, max_v = get_h_distance_metrics(unit.word_list)
                            phrase_data[n_ph][pos]['h_dist_avg'].append(avg_v)
                            phrase_data[n_ph][pos]['h_dist_med'].append(med_v)
                            phrase_data[n_ph][pos]['h_dist_max'].append(max_v)

                    # --- SUBPHRASES (Big Chunks) ---
                    if all_subphrases:
                        #sorted_sp = sorted(all_subphrases, key=lambda u: min([w.id for w in u.word_list]))
                        sorted_sp = sorted(all_subphrases, key=lambda u: statistics.mean([w.id for w in u.word_list]))
                        n_sp = len(sorted_sp)
                        subphrase_data[n_sp]['parent_sizes'].append(n_sp)
                        for pos, unit in enumerate(sorted_sp):
                            avg_v, med_v, max_v = get_h_distance_metrics(unit.word_list)
                            subphrase_data[n_sp][pos]['h_dist_avg'].append(avg_v)
                            subphrase_data[n_sp][pos]['h_dist_med'].append(med_v)
                            subphrase_data[n_sp][pos]['h_dist_max'].append(max_v)

                    # --- CHUNKS ---
                    if all_chunks:
                        #sorted_ch = sorted(all_chunks, key=lambda u: min([w.id for w in u.word_list]))
                        sorted_ch = sorted(all_chunks, key=lambda u: statistics.mean([w.id for w in u.word_list]))
                        n_ch = len(sorted_ch)
                        chunk_data[n_ch]['parent_sizes'].append(n_ch)
                        for pos, unit in enumerate(sorted_ch):
                            avg_v, med_v, max_v = get_h_distance_metrics(unit.word_list)
                            chunk_data[n_ch][pos]['h_dist_avg'].append(avg_v)
                            chunk_data[n_ch][pos]['h_dist_med'].append(med_v)
                            chunk_data[n_ch][pos]['h_dist_max'].append(max_v)

    # Apply Merging with Tail-Folding
    #main_clause_data = merge_outliers(main_clause_data, w_sentence)
    #clause_data = merge_outliers(clause_data, w_main_clause)
    phrase_data = merge_outliers(phrase_data, w_phrase)
    subphrase_data = merge_outliers(subphrase_data, w_big_chunk)
    chunk_data = merge_outliers(chunk_data, w_chunk)

    if not os.path.exists(output_folder): os.makedirs(output_folder)

    # Helper function to bulk-export the 3 metrics per category
    def export_group(data, prefix):
        export_to_csv(data, os.path.join(output_folder, f'{prefix}_hdist_mean.csv'), 'h_dist_avg', 'Mean h_dist')
        export_to_csv(data, os.path.join(output_folder, f'{prefix}_hdist_median.csv'), 'h_dist_med', 'Median h_dist')
        export_to_csv(data, os.path.join(output_folder, f'{prefix}_hdist_max.csv'), 'h_dist_max', 'Max h_dist')

    # Export Categories
    #export_group(main_clause_data, f'{file_name}_main_clause')
    #export_group(clause_data, f'{file_name}_clauses')
    export_group(phrase_data, f'{file_name}_phrases')
    export_group(subphrase_data, f'{file_name}_subphrases')
    export_group(chunk_data, f'{file_name}_chunks')


if __name__ == "__main__":
    pickle_list = [f for f in os.listdir(main_directory) if f.endswith('.pkl')]
    for p_file in pickle_list:
        name = p_file.replace('.pkl', '')
        treebank = SUD_parser_main_clause.load_treebank_pkl(os.path.join(main_directory, p_file))
        characteristics_units(treebank, path_all, name)
    print("Done!")