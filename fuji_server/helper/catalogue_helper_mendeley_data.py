import logging

import requests

from fuji_server.helper.catalogue_helper import MetaDataCatalogue


class MetaDataCatalogueMendeleyData(MetaDataCatalogue):
    """A class to access Mendeley Data metadata catalogue
    Attributes
    ----------
    isListed : bool
        Boolean to check whether the metadata is listed in the metadata catalog
    apiURI : str
        The URI for API of metadata catalogue

    Methods
    -------
    query(pidlist)
        Method to check whether the metadata given by PID is listed in Mendeley Data
    """

    islisted = False
    apiURI = "https://api.datasearch.elsevier.com/api/v2/search?query="

    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger
        self.source = self.getEnumSourceNames().MENDELEY_DATA.value

    def query(self, pidlist):
        """Method to check whether the metadata given by PID is listed in Mendeley Data
        Parameters
        ----------
        pidlist:list
            A list of PID

        Returns
        -------
        response
            session response
        """
        response = None
        for pid in pidlist:
            try:
                if pid:
                    res = requests.get(self.apiURI + "/" + requests.utils.quote(str(pid)), timeout=1)
                    self.logger.info("FsF-F4-01M : Querying Mendeley Data API for -:" + str(pid))
                    if res.status_code == 200:
                        resp = res.json()
                        if resp.get("results"):
                            for result in resp.get("results"):
                                if (
                                    str(pid).lower() == str(result.get("doi")).lower()
                                    or str(pid).lower() == str(result.get("containerURI")).lower()
                                ):
                                    self.islisted = True
                                    self.logger.info(
                                        "FsF-F4-01M : Found identifier in Mendeley Data catalogue -:" + str(pid)
                                    )
                                    break
                            if not self.islisted:
                                self.logger.info(
                                    "FsF-F4-01M : Identifier not listed in Mendeley Data catalogue -:" + str(pid)
                                )

                    else:
                        self.logger.error("FsF-F4-01M : Mendeley Data API not available -:" + str(res.status_code))
            except Exception as e:
                self.logger.error("FsF-F4-01M : Mendeley Data API not available or returns errors: " + str(e))

        return response
