from Bio.Blast import NCBIXML

def parse_blast_results(blast_results):
    """解析 BLAST XML 结果并返回结构化摘要。"""
    blast_records = NCBIXML.parse(blast_results)
    parsed_results = []

    for blast_record in blast_records:
        for alignment in blast_record.alignments:
            for hsp in alignment.hsps:
                parsed_results.append({
                    "title": alignment.title,
                    "length": alignment.length,
                    "score": hsp.score,
                    "e_value": hsp.expect,
                    "query_start": hsp.query_start,
                    "query_end": hsp.query_end,
                    "qseq": hsp.query,
                    "match": hsp.match,
                    "hseq": hsp.sbjct
                })

    return parsed_results