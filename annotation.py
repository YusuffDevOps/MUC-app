import sys
import os
import csv
import shutil
import tempfile
import datetime

from pathlib import Path

from bakta import Bakta
from rgi import Rgi


def write_info_in_annotation_file(
        annotation_writer, gene_info, no_RGI, len_seq=None
):
    """
    To write annotation details into files
    Parameters:
        annotation_writer:	annotation file containing all annotations
        seq_description: a small description of the sequence used for naming
        seq: the extracted dna sequence that has been annotated
        gene_info: annotation info
        contig_name: the name of contig matching this extracted sequence (if there is any contig)
        no_RGI: if True, RGI has not been used to annotate AMRs
        found: if True, the annotation info has already found in other annotated sequences
    """
    seq = gene_info["seq_value"]
    if len_seq is None:
        len_seq = len(seq)
    if not no_RGI:
        annotation_writer.writerow(
            [
                seq,
                len_seq,
                gene_info["gene"],
                gene_info["product"],
                gene_info["length"],
                gene_info["start_pos"],
                gene_info["end_pos"],
                gene_info["RGI_prediction_type"],
                gene_info["family"],
            ]
        )
    else:
        annotation_writer.writerow(
            [
                seq,
                len_seq,
                gene_info["gene"],
                gene_info["product"],
                gene_info["length"],
                gene_info["start_pos"],
                gene_info["end_pos"],
            ]
        )

def create_fasta_file(seq, output_dir, comment="> sequence:\n", file_name="temp"):
    """
    To create a fasta file for a sequence
    Parameters:
        seq: the sequence to be written into the file
        output_dir: the output directory address
        comment: the comment to be written into fasta file
        file_name: the name of the fasta file
    Return:
        the address of the fasta file
    """
    myfile_name = os.path.join(output_dir, file_name + ".fasta")
    if os.path.isfile(myfile_name):
        os.remove(myfile_name)
    with open(myfile_name, 'w') as myfile:
        myfile.write(comment)
        if not comment.endswith("\n"):
            myfile.write("\n")
        myfile.write(seq)
        if not seq.endswith("\n"):
            myfile.write("\n")
    return myfile_name

def run_RGI(
        input_file, output_dir, seq_description, include_loose=False, delete_rgi_files=False
):
    """
    To run RGI and annotate AMRs in the sequence
    # To ensure consistency between Prokka and RGI findings, we annotate found proteins
    # by Prokka (instead of annotationg DNA sequences from scratch)
    Parameters:
        input_file: the file contating proteins annotated by Prokka
        output_dir:  the path for the output directory
        seq_description: a small description of the sequence used for naming
        include_loose: Whether to include loose annotations
    Return:
        the list of extracted annotation information for the sequence
    """
    rgi_dir = os.path.join(output_dir, "rgi_dir")
    os.makedirs(rgi_dir, exist_ok=True)

    output_file_name = os.path.join(
        rgi_dir,
        "rgi_output_"
        + seq_description
        + "_"
        + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M"),
    )
    # remove any potential * from the sequence
    # delete_a_string_from_file("*", input_file) # TODO: Not used?

    rgi = Rgi.run_for_sarand(
        input_sequence=Path(input_file),
        output_file=Path(output_file_name),
        include_loose=include_loose,
    )

    # delete temp files
    if delete_rgi_files and os.path.isfile(output_file_name + ".txt"):
        os.remove(output_file_name + ".txt")
    if delete_rgi_files and os.path.isfile(output_file_name + ".json"):
        os.remove(output_file_name + ".json")

    return rgi.result.data

def annotate_sequence(
        seq,
        seq_description,
        output_dir,
        no_RGI=False,
        RGI_include_loose=False,
        delete_prokka_dir=False,
):
    """
    To run Prokka/BAKTA for a sequence and extract required information from its
        generated output files
    Parameters:
        seq:	the sequence to be annotated
        seq_description: a small description of the sequence used for naming
        output_dir:  the path for the output directory
        no_RGI:	RGI annotations incorporated for AMR annotation
    Return:
        the list of extracted annotation information for the sequence
    """
    # write the sequence into a temporary file
    with tempfile.TemporaryDirectory() as tmp_dir:
        seq_file_name = create_fasta_file(
            seq,
            tmp_dir,
            file_name="temp_"
                      + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                      + seq_description,
        )
        pid = os.getpid()
        prokka_dir = (
                "bakta_dir_"
                + seq_description
                + "_"
                + str(pid)
                + "_"
                + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
        )
        prefix_name = "neighbourhood_" + seq_description

        # Run Bakta
        ba = Bakta.run_for_sarand(
            genome=Path(seq_file_name),
            prefix=prefix_name,
            out_dir=Path(output_dir) / prokka_dir,
        )

    # This re-appends the sequence as per the original implementation, however
    # this could be extracted from the JSON
    seq_info = ba.result.get_for_sarand()
    for seq_info_new_item in seq_info:
        seq_info_new_item['seq_value'] = seq[:-1]

    RGI_output_list = None
    if not no_RGI:
        RGI_output_list = run_RGI(
            str(ba.params.path_faa.absolute()),
            output_dir,
            seq_description,
            RGI_include_loose,
            delete_prokka_dir,
        )

    # incorporate RGI findings into Prokka's
    if RGI_output_list:
        for item in RGI_output_list:
            for gene_info in seq_info:
                if item["ORF_ID"].split(" ")[0] == gene_info["locus_tag"]:
                    gene_info["gene"] = item["gene"]
                    gene_info["RGI_prediction_type"] = item["prediction_type"]
                    gene_info["family"] = item["family"]
                    break

    # remove temporary files and folder
    # if os.path.isfile(seq_file_name):
    #     os.remove(seq_file_name)
    if delete_prokka_dir:
        try:
            shutil.rmtree(prokka_dir)
        except OSError as e:
            print("Error: %s - %s." % (e.filename, e.strerror))

    return seq_info

def extract_seq_annotation(annotate_dir, no_RGI, RGI_include_loose, seq_pair):
    """
    The function used in parallel anntation to call the function for annotating a sequence
    Parameters:
        annotate_dir: the directory to store annotation output
        no_RGI: if True we want to call RGI for annotating AMRs
        RGI_include_loose: if True loose mode is used
        seq_pair: the index and the value of a sequence to be annotated
    Return:
        the list of annotated genes
    """
    counter, ext_seq = seq_pair
    seq_description = "extracted" + str(counter)
    seq_info_list = annotate_sequence(
        ext_seq,
        seq_description,
        annotate_dir,
        no_RGI,
        RGI_include_loose,
    )
    return seq_info_list


def extract_graph_seqs_annotation(
        neighborhood_seq_file,
        annotate_dir,
        core_num,
        no_RGI,
        RGI_include_loose,
        annotation_writer,
):
    """
    To annotate neighborhood sequences of AMR extracted from the graph in parallel
    Parameters:
        neighborhood_seq_file: the file containing extracted sequences
        annotate_dir: the directory to sore annotation results
        core_num: the number of core for parallel processing
        no_RGI: if True RGI is not used for AMR annotation
        RGI_include_loose: if True use loose mode in RGI
        annotation_writer: the file to store annotation results
    Return:
        the list of annotated genes and their details
    """
    # find the list of all extracted sequences
    print("Reading seq file")
    sequence_list = []
    counter = 1
    with open(neighborhood_seq_file, "r") as read_obj:
        for line in read_obj:
            sequence_list.append((counter, line))
            counter += 1

    # Parallel annotation
    """
    AM: Do not initialise a multiprocessing pool if only one thread is required.
    """
    if core_num == 1:
        seq_info_list = list()
        for x in sequence_list:
            seq_info_list.append(extract_seq_annotation(annotate_dir, no_RGI, RGI_include_loose, x))
    else:
        p_annotation = partial(
            extract_seq_annotation, annotate_dir, no_RGI, RGI_include_loose
        )
        with Pool(core_num) as p:
            seq_info_list = p.map(p_annotation, sequence_list)

    # Further processing of result of parallel annotation
    for i, seq_info in enumerate(seq_info_list):
        # write annotation onfo into the files
        for j, gene_info in enumerate(seq_info):
            write_info_in_annotation_file(
                annotation_writer, gene_info, no_RGI
            )
    return seq_info_list

def neighborhood_annotation(
        neighborhood_seq_file,
        output_dir,
        no_RGI=False,
        RGI_include_loose=False,
        output_name="",
        core_num=4,
):
    """
    To annotate reference genomes sequences, and summarize the results
        in a couple of formats
    Parameters:
        neighborhood_seq_file:	the address of the file containing all extracted
             neighborhood sequences from assembly graph
        output_dir:	the path for the output directory
        no_RGI:	RGI annotations not incorporated for AMR annotation
        RGI_include_loose: Whether to include loose annotaions in RGI
        output_name:the name used to distinguish different output files usually based on the name of AMR
    Return:
        the address of files stroing annotation information (annotation_detail_name,
            trimmed_annotation_info, gene_file_name, visual_annotation)
    """
    # initializing required files and directories
    annotate_dir = os.path.join(
        output_dir,
        "annotation" + output_name,
    )
    if os.path.exists(annotate_dir):
        try:
            shutil.rmtree(annotate_dir)
        except OSError as e:
            print("Error: %s - %s." % (e.filename, e.strerror))
    os.makedirs(annotate_dir)
    annotation_detail_name = os.path.join(
        annotate_dir, "annotation_detail" + output_name + ".csv"
    )
    annotation_detail = open(annotation_detail_name, mode="w", newline="")
    annotation_writer = csv.writer(annotation_detail)
    gene_info = {
        "seq_value": "seq_value",
        "gene": "gene",
        "product": "product",
        "length": "length",
        "start_pos": "start_pos",
        "end_pos": "end_pos",
        "RGI_prediction_type": "RGI_prediction_type",
        "family": "family",
    }
    write_info_in_annotation_file(
        annotation_writer,
        gene_info,
        no_RGI,
        "seq_length",
    )

    # annotate the sequences extraced from assembly graph
    all_seq_info_list = extract_graph_seqs_annotation(
        neighborhood_seq_file,
        annotate_dir,
        core_num,
        no_RGI,
        RGI_include_loose,
        annotation_writer,
    )
    print(
        "The comparison of neighborhood sequences are available in "
        + annotation_detail_name
    )
    annotation_detail.close()

    return all_seq_info_list, annotation_detail_name


sequence_file = sys.argv[1]
output_dir = sys.argv[2]
all_seq_info_list, annotation_file = neighborhood_annotation(
            sequence_file,
            output_dir,
            False,
            False,
            "sequence" ,
            1,
)
