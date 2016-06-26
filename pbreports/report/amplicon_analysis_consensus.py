#!/usr/bin/env python
"""Summarizes the Long Amplicon Analysis"""

import os
import os.path as op
import sys
import logging
from pprint import pformat

import numpy as np

from pbcommand.models.report import Report, Table, Column
from pbreports.report.report_spec import (MetaAttribute, MetaPlotGroup, MetaPlot,
                                          MetaColumn, MetaTable, MetaReport)
from pbcommand.models import FileTypes, get_pbparser
from pbcommand.cli import pbparser_runner
from pbcommand.common_options import add_debug_option
from pbcommand.utils import setup_log

from pbreports.util import recfromcsv
from pbreports.util import validate_nonempty_file


log = logging.getLogger(__name__)

__version__ = '0.3.1'

# Import Mapping MetaReport
_DIR_NAME = os.path.dirname(os.path.realpath(__file__))
SPEC_DIR = os.path.join(_DIR_NAME, 'specs/')
AAC_SPEC = op.join(SPEC_DIR, 'amplicon_analysis_consensus.json')
meta_rpt = MetaReport.from_json(AAC_SPEC)


class Constants(object):
    TOOL_ID = "pbreports.tasks.amplicon_analysis_consensus"


def create_table(d, barcode):
    """Long Amplicon Analysis results table"""

    columns = []

    if barcode:
        columns.append(Column("barcodename", header = ""))

    columns.append(Column("coarsecluster", header = ""))
    columns.append(Column("phase", header = ""))
    columns.append(Column("sequencelength", header = ""))
    columns.append(Column("predictedaccuracy", header = ""))
    columns.append(Column("totalcoverage", header = ""))

    t = Table("result_table",
              columns=columns)

    for fastaname in sorted(d.fastaname):
        row = d[d.fastaname == fastaname]
        for column in columns:
            # if column.id == "predictedaccuracy":
            #    accuracy = round(100 * row[column.id][0], 2)
            #    t.add_data_by_column_id(column.id, accuracy)
            # else:
            t.add_data_by_column_id(column.id, row[column.id][0])

    log.info(str(t))
    return t


def run_to_report(summary_file):
    log.info("Generating report v{v} from file: {f}".format(f=summary_file,
                                                            v=__version__))

    s = recfromcsv(summary_file)

    # Check whether we need
    barcode = False
    if np.unique(s.barcodename).shape[0] > 1:
        barcode = True

    # Filter out noise and chimera sequences
    try:
        s = s[s.noisesequence == False]
        s = s[s.ischimera == False]
    except AttributeError:
        # XXX not yet implemented
        pass

    # Convert the data to a table and the report
    table = create_table(s, barcode)
    r = Report(meta_rpt.id, tables=[table])

    return meta_rpt.apply_view(r)


def amplicon_analysis_consensus(incsv, outjson):
    log.info("Running {f} v{v}.".format(
        f=os.path.basename(__file__), v=__version__))
    report = run_to_report(incsv)
    log.info(pformat(report.to_dict()))
    report.write_json(outjson)
    return 0


def args_runner(args):
    validate_nonempty_file(args.report_csv)
    amplicon_analysis_consensus(args.report_csv, args.report_json)
    return 0


def resolved_tool_contract_runner(resolved_tool_contract):
    rtc = resolved_tool_contract
    amplicon_analysis_consensus(rtc.task.input_files[0],
                                rtc.task.output_files[0])
    return 0


def _add_options_to_parser(p):
    p.add_input_file_type(
        FileTypes.CSV,
        file_id="report_csv",
        name="ConsensusReportCSV",
        description="Consensus Report CSV")
    p.add_output_file_type(
        FileTypes.REPORT,
        file_id="report_json",
        name="Amplicon consensus report",
        description="Amplicon Consensus Report JSON",
        default_name="consensus_report")


def add_options_to_parser(p):
    """
    API function for extending main pbreport arg parser (independently of
    tool contract interface).
    """
    p_wrap = _get_parser_core()
    p_wrap.arg_parser.parser = p
    p.description = __doc__
    add_debug_option(p)
    _add_options_to_parser(p_wrap)
    p.set_defaults(func=args_runner)
    return p


def _get_parser_core():
    driver_exe = ("python -m "
                  "pbreports.report.amplicon_analysis_consensus "
                  "--resolved-tool-contract ")
    p = get_pbparser(
        Constants.TOOL_ID,
        __version__,
        meta_rpt.title,
        __doc__,
        driver_exe)
    return p


def get_parser():
    p = _get_parser_core()
    _add_options_to_parser(p)
    return p


def main(argv=sys.argv):
    mp = get_parser()
    return pbparser_runner(argv[1:],
                           mp,
                           args_runner,
                           resolved_tool_contract_runner,
                           log,
                           setup_log)

# for 'python -m pbreports.report.amplicon_analysis_consensus ...'
if __name__ == "__main__":
    sys.exit(main())
