import os
import csv
import statistics
from collections import defaultdict
import SUD_parser_main_clause


"""The embedding distance vs position with 0.1% merging. 
Calculates the Mean, Median, and Max of word.h_distance for units at various hierarchy levels.
Stops at the Chunk level (processes only primary chunk_list, no word-level output)."""

# --- CONFIGURATION ---
main_directory = 'C:/Users/nogol/Documents/Doktorat/corpora240717/SUD/processed/260403_saved/'
path_all = 'C:/Users/nogol/Documents/Doktorat/Analyzy/SUD/vysledky260403/Characteristics/h_distance_vs_position/sort_by_mean_id'


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
    dists = [w.h_distance for w in word_list if getattr(w, 'h_distance', None) is not None]
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

    main_clause_data = defaultdict(factory)
    clause_data = defaultdict(factory)
    phrase_data = defaultdict(factory)
    subphrase_data = defaultdict(factory)
    chunk_data = defaultdict(factory)

    for sentence in a_treebank.sentence_list:
        if sentence.root_good and not sentence.bad_things and sentence.num_conj <= 1:

            # --- 1. SENTENCE LEVEL ---
            v_main_clauses = [mc for mc in sentence.main_clause_list if len(mc.word_list) > 0]
            if v_main_clauses:
                #sorted_mc = sorted(v_main_clauses, key=lambda mc: min([w.id for w in mc.word_list]))
                sorted_mc = sorted(v_main_clauses, key=lambda mc: statistics.mean([w.id for w in mc.word_list]))
                n_s = len(sorted_mc)
                main_clause_data[n_s]['parent_sizes'].append(n_s)

                for s_i, mc in enumerate(sorted_mc):
                    avg_v, med_v, max_v = get_h_distance_metrics(mc.word_list)
                    main_clause_data[n_s][s_i]['h_dist_avg'].append(avg_v)
                    main_clause_data[n_s][s_i]['h_dist_med'].append(med_v)
                    main_clause_data[n_s][s_i]['h_dist_max'].append(max_v)

                    # --- 2. MAIN CLAUSE LEVEL ---
                    v_clauses = [cl for cl in mc.clause_list if len(cl.word_list) > 0]
                    if v_clauses:
                        #sorted_cl = sorted(v_clauses, key=lambda cl: min([w.id for w in cl.word_list]))
                        sorted_cl = sorted(v_clauses, key=lambda cl: statistics.mean([w.id for w in cl.word_list]))
                        n_mc = len(sorted_cl)
                        clause_data[n_mc]['parent_sizes'].append(n_mc)

                        for m_i, clause in enumerate(sorted_cl):
                            avg_v, med_v, max_v = get_h_distance_metrics(clause.word_list)
                            clause_data[n_mc][m_i]['h_dist_avg'].append(avg_v)
                            clause_data[n_mc][m_i]['h_dist_med'].append(med_v)
                            clause_data[n_mc][m_i]['h_dist_max'].append(max_v)

                            # --- 3. CLAUSE LEVEL (Phrases) ---
                            v_phrases = [p for p in clause.phrase_list if len(p.word_list) > 0]
                            if v_phrases:
                                #sorted_p = sorted(v_phrases, key=lambda p: p.root_phrase.id if p.root_phrase else min([w.id for w in p.word_list]))
                                #sorted_p = sorted(v_phrases, key=lambda p: min([w.id for w in p.word_list]))
                                sorted_p = sorted(v_phrases, key=lambda p: statistics.mean([w.id for w in p.word_list]))
                                n_cl = len(sorted_p)
                                phrase_data[n_cl]['parent_sizes'].append(n_cl)

                                for p_i, p in enumerate(sorted_p):
                                    avg_v, med_v, max_v = get_h_distance_metrics(p.word_list)
                                    #print("max_v", max_v)
                                    phrase_data[n_cl][p_i]['h_dist_avg'].append(avg_v)
                                    phrase_data[n_cl][p_i]['h_dist_med'].append(med_v)
                                    phrase_data[n_cl][p_i]['h_dist_max'].append(max_v)

                                    # --- 4. PHRASE LEVEL (Subphrases) ---
                                    v_sub = [sp for sp in p.big_chunk_list if len(sp.word_list) > 0]
                                    if v_sub:
                                        #sorted_s = sorted(v_sub, key=lambda sp: sp.root_BigChunk.id if sp.root_BigChunk else min([w.id for w in sp.word_list]))
                                        sorted_s = sorted(v_sub, key=lambda sp: statistics.mean([w.id for w in sp.word_list]))
                                        ns = len(sorted_s)
                                        subphrase_data[ns]['parent_sizes'].append(ns)

                                        for sp_i, sp in enumerate(sorted_s):
                                            avg_v, med_v, max_v = get_h_distance_metrics(sp.word_list)
                                            subphrase_data[ns][sp_i]['h_dist_avg'].append(avg_v)
                                            subphrase_data[ns][sp_i]['h_dist_med'].append(med_v)
                                            subphrase_data[ns][sp_i]['h_dist_max'].append(max_v)

                                            # --- 5. CHUNK LEVEL ---
                                            v_ch = [ch for ch in sp.chunk_list if len(ch.word_list) > 0]
                                            if v_ch:
                                                #sorted_ch = sorted(v_ch, key=lambda ch: min([w.id for w in ch.word_list]))
                                                sorted_ch = sorted(v_ch,key=lambda ch: statistics.mean([w.id for w in ch.word_list]))
                                                nc = len(sorted_ch)
                                                chunk_data[nc]['parent_sizes'].append(nc)

                                                for c_i, ch in enumerate(sorted_ch):
                                                    avg_v, med_v, max_v = get_h_distance_metrics(ch.word_list)
                                                    chunk_data[nc][c_i]['h_dist_avg'].append(avg_v)
                                                    chunk_data[nc][c_i]['h_dist_med'].append(med_v)
                                                    chunk_data[nc][c_i]['h_dist_max'].append(max_v)

    # Apply Merging with Tail-Folding
    main_clause_data = merge_outliers(main_clause_data, w_sentence)
    clause_data = merge_outliers(clause_data, w_main_clause)
    phrase_data = merge_outliers(phrase_data, w_clause)
    subphrase_data = merge_outliers(subphrase_data, w_phrase)
    chunk_data = merge_outliers(chunk_data, w_big_chunk)

    if not os.path.exists(output_folder): os.makedirs(output_folder)

    # Helper function to bulk-export the 3 metrics per category
    def export_group(data, prefix):
        export_to_csv(data, os.path.join(output_folder, f'{prefix}_hdist_mean.csv'), 'h_dist_avg', 'Mean h_dist')
        export_to_csv(data, os.path.join(output_folder, f'{prefix}_hdist_median.csv'), 'h_dist_med', 'Median h_dist')
        export_to_csv(data, os.path.join(output_folder, f'{prefix}_hdist_max.csv'), 'h_dist_max', 'Max h_dist')

    # Export Categories
    export_group(main_clause_data, f'{file_name}_main_clause')
    export_group(clause_data, f'{file_name}_clauses')
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