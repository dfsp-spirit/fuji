# MIT License
#
# Copyright (c) 2020 PANGAEA (https://www.pangaea.de/)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import mimetypes
import re

from fuji_server.evaluators.fair_evaluator import FAIREvaluator
from fuji_server.models.data_file_format import DataFileFormat
from fuji_server.models.data_file_format_output import DataFileFormatOutput
from fuji_server.models.data_file_format_output_inner import DataFileFormatOutputInner


class FAIREvaluatorFileFormat(FAIREvaluator):
    """
    A class to evaluate whether the data is available in a file format recommended by the targe research community (R1.3-02D).
    A child class of FAIREvaluator.
    ...

    Methods
    -------
    evaluate()
        This method will evaluate whether the data format is available in a long-term format (as defined in ISO/TR 22299)
        or in open format (see e.g., https://en.wikipedia.org/wiki/List_of_open_formats) or in a scientific file format.
    """

    def __init__(self, fuji_instance):
        FAIREvaluator.__init__(self, fuji_instance)
        self.set_metric("FsF-R1.3-02D")
        self.data_file_list = []

    def setFileFormatDict(self):
        mime_url_pair = {}
        if not self.fuji.content_identifier:  # self.content_identifier only includes uris that are accessible
            contents = self.fuji.metadata_merged.get("object_content_identifier")
            unverified_content_urls = []
            if contents:
                for c in contents:
                    if c.get("type"):
                        if c.get("url"):
                            unverified_content_urls.append(c.get("url"))
                            mime_url_pair[c.get("type")] = c.get("url")
                if unverified_content_urls:
                    self.logger.info(
                        f"FsF-R1.3-02D : Data content (inaccessible) identifier provided -: -: {list(set(unverified_content_urls))}"
                    )
        elif len(self.fuji.content_identifier) > 0:
            verified_content_urls = [item.get("url") for item in self.fuji.content_identifier.values()]
            self.logger.info(f"FsF-R1.3-02D : Data content identifier provided -: {verified_content_urls}")
            # self.maturity = 1
            for file_index, data_file in enumerate(self.fuji.content_identifier.values()):
                mime_type = data_file.get("claimed_type")
                # print(data_file)
                if data_file.get("url") is not None:
                    if (mime_type is None or "/" not in mime_type) and data_file.get("header_content_type"):
                        self.logger.info(
                            "FsF-R1.3-02D : No mime type given in metadata, therefore the mime type given in HTTP header is used -: {}".format(
                                data_file.get("header_content_type")
                            )
                        )
                        mime_type = data_file.get("header_content_type")
                    if (
                        mime_type is None
                        or "/" not in mime_type
                        or mime_type in ["application/octet-stream", "binary/octet-stream"]
                    ):
                        self.logger.info(
                            "FsF-R1.3-02D : No mime type given in metadata or generic octet-stream type given, therefore guessing  the type of a file based on its filename or URL -: {}".format(
                                data_file.get("url")
                            )
                        )
                        # if mime type not given try to guess it based on the file name
                        guessed_mime_type = mimetypes.guess_type(data_file.get("url"))
                        mime_type = guessed_mime_type[
                            0
                        ]  # the return value is a tuple (type, encoding) where type is None if the type can`t be guessed
                        if mime_type:
                            self.logger.info(f"FsF-R1.3-02D : Mime type guess return value -: {mime_type}")
                        else:
                            self.logger.info("FsF-R1.3-02D : Failed to guess mime type based on file name")

                    if mime_type:
                        self.logger.info("FsF-R1.3-02D : Found mime type in metadata -: " + str(mime_type))
                        valid_type = True
                        if data_file.get("tika_content_type"):
                            if mime_type not in data_file.get("tika_content_type"):
                                valid_type = False
                        if mime_type in self.fuji.ARCHIVE_MIMETYPES:  # check archive&compress media type
                            self.logger.info(f"FsF-R1.3-02D : Archiving/compression format specified -: {mime_type}")
                            if valid_type and data_file.get("tika_content_type"):
                                # exclude archive format
                                # if file_index == len(self.fuji.content_identifier) - 1:
                                data_file["tika_content_type"] = [
                                    n
                                    for n in data_file.get("tika_content_type")
                                    if n not in self.fuji.ARCHIVE_MIMETYPES
                                ]
                                self.logger.info(
                                    "FsF-R1.3-02D : Extracted file formats for selected data object (see FsF-R1-01MD) -: {}".format(
                                        data_file.get("tika_content_type")
                                    )
                                )
                                for t in data_file.get("tika_content_type"):
                                    mime_url_pair[t] = data_file.get("url")
                            else:
                                self.logger.warning(
                                    "FsF-R1.3-02D : Content type not verified during FsF-R1-01MD, assuming login page or similar instead of -: {}".format(
                                        mime_type
                                    )
                                )
                        else:
                            mime_url_pair[mime_type] = data_file.get("url")
                            if data_file.get("tika_content_type"):
                                # add tika detected mimes
                                for tika_mime in data_file.get("tika_content_type"):
                                    if valid_type and tika_mime not in mime_url_pair:
                                        mime_url_pair[tika_mime] = data_file.get("url")
        return mime_url_pair

    def testCommunityFileFormatUsed(self, mime_url_pair):
        # FILE FORMAT CHECKS....
        # check if format is a scientific one:
        preferred_mimetype = None
        text_format_regex = r"(^text)[\/]|[\/\+](xml|text|json)"
        test_status = False
        if self.isTestDefined(self.metric_identifier + "-1"):
            test_score = self.getTestConfigScore(self.metric_identifier + "-1")
            if mime_url_pair:
                for mimetype, url in mime_url_pair.items():
                    data_file_output = DataFileFormatOutputInner()
                    preferance_reason = []
                    subject_area = []
                    if mimetype in self.fuji.SCIENCE_FILE_FORMATS:
                        self.setEvaluationCriteriumScore("FsF-R1.3-02D-1c", 0, "pass")
                        if self.maturity < self.getTestConfigMaturity("FsF-R1.3-02D-1c"):
                            self.maturity = self.getTestConfigMaturity("FsF-R1.3-02D-1c")
                        if self.fuji.SCIENCE_FILE_FORMATS.get(mimetype) == "Generic":
                            subject_area.append("General")
                            preferance_reason.append("generic science format")
                        else:
                            subject_area.append(self.fuji.SCIENCE_FILE_FORMATS.get(mimetype))
                            preferance_reason.append("science format")
                        test_status = data_file_output.is_preferred_format = True

                    # check if long term format
                    if mimetype in self.fuji.LONG_TERM_FILE_FORMATS:
                        self.setEvaluationCriteriumScore("FsF-R1.3-02D-1b", 0, "pass")
                        if self.maturity < self.getTestConfigMaturity("FsF-R1.3-02D-1b"):
                            self.maturity = self.getTestConfigMaturity("FsF-R1.3-02D-1b")
                        preferance_reason.append("long term format")
                        subject_area.append("General")
                        test_status = data_file_output.is_preferred_format = True
                    # check if open format
                    if mimetype in self.fuji.OPEN_FILE_FORMATS:
                        self.setEvaluationCriteriumScore("FsF-R1.3-02D-1a", 0, "pass")
                        if self.maturity < self.getTestConfigMaturity("FsF-R1.3-02D-1a"):
                            self.maturity = self.getTestConfigMaturity("FsF-R1.3-02D-1a")
                        preferance_reason.append("open format")
                        subject_area.append("General")
                        test_status = data_file_output.is_preferred_format = True
                    # generic text/xml/json file check

                    if "html" not in mimetype and re.search(text_format_regex, mimetype):
                        self.setEvaluationCriteriumScore("FsF-R1.3-02D-1a", 0, "pass")
                        self.setEvaluationCriteriumScore("FsF-R1.3-02D-1b", 0, "pass")
                        self.setEvaluationCriteriumScore("FsF-R1.3-02D-1c", 0, "fail")
                        self.maturity = self.getTestConfigMaturity("FsF-R1.3-02D-1b")
                        preferance_reason.extend(["long term format", "open format", "generic science format"])
                        subject_area.append("General")
                        test_status = data_file_output.is_preferred_format = True
                    if "html" in mimetype:
                        preferance_reason = []

                    if preferance_reason:
                        preferred_mimetype = mimetype
                        self.logger.log(
                            self.fuji.LOG_SUCCESS,
                            "FsF-R1.3-02D : Could identify a file format commonly used by the scientific community -:"
                            + str(preferred_mimetype),
                        )
                    data_file_output.mime_type = mimetype
                    data_file_output.file_uri = url
                    data_file_output.preference_reason = list(set(preferance_reason))
                    data_file_output.subject_areas = list(set(subject_area))
                    self.data_file_list.append(data_file_output)
        if test_status:
            self.score.earned = test_score
            self.setEvaluationCriteriumScore("FsF-R1.3-02D-1", test_score, "pass")
        return test_status

    def evaluate(self):
        self.result = DataFileFormat(
            id=self.metric_number, metric_identifier=self.metric_identifier, metric_name=self.metric_name
        )
        self.output = DataFileFormatOutput()
        mime_url_dict = self.setFileFormatDict()
        if self.testCommunityFileFormatUsed(mime_url_dict):
            self.result.test_status = "pass"
        else:
            self.logger.warning(
                "FsF-R1.3-02D : Could not perform file format checks as data content identifier(s) unavailable/inaccesible"
            )
            self.result.test_status = "fail"

        self.output = self.data_file_list
        self.result.output = self.output
        self.result.metric_tests = self.metric_tests
        self.result.maturity = self.maturity
        self.result.score = self.score
