from fuji_server import util
from fuji_server.models.base_model_ import Model


class StandardisedProtocolMetadataOutput(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    def __init__(self, standard_metadata_protocol: str | None = None):
        """StandardisedProtocolMetadataOutput - a model defined in Swagger

        :param standard_metadata_protocol: The standard_metadata_protocol of this StandardisedProtocolMetadataOutput.  # noqa: E501
        :type standard_metadata_protocol: str
        """
        self.swagger_types = {"standard_metadata_protocol": str}

        self.attribute_map = {"standard_metadata_protocol": "standard_metadata_protocol"}
        self._standard_metadata_protocol = standard_metadata_protocol

    @classmethod
    def from_dict(cls, dikt) -> "StandardisedProtocolMetadataOutput":
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The StandardisedProtocolMetadata_output of this StandardisedProtocolMetadataOutput.  # noqa: E501
        :rtype: StandardisedProtocolMetadataOutput
        """
        return util.deserialize_model(dikt, cls)

    @property
    def standard_metadata_protocol(self) -> str:
        """Gets the standard_metadata_protocol of this StandardisedProtocolMetadataOutput.


        :return: The standard_metadata_protocol of this StandardisedProtocolMetadataOutput.
        :rtype: str
        """
        return self._standard_metadata_protocol

    @standard_metadata_protocol.setter
    def standard_metadata_protocol(self, standard_metadata_protocol: str):
        """Sets the standard_metadata_protocol of this StandardisedProtocolMetadataOutput.


        :param standard_metadata_protocol: The standard_metadata_protocol of this StandardisedProtocolMetadataOutput.
        :type standard_metadata_protocol: str
        """

        self._standard_metadata_protocol = standard_metadata_protocol
