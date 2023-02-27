import gzip
import io
import warnings
from typing import List, Tuple

import pandas as pd
from astropy.io import fits
from astropy.utils.exceptions import AstropyWarning
from astropy.wcs import WCS
from atlas_stamp_classifier.inference import AtlasStampClassifier

from .base import BaseStrategy


class ATLASStrategy(BaseStrategy):
    FIELDS = ["candid", "mjd"]
    HEADER_FIELDS = ["FILTER", "AIRMASS", "SEEING", "SUNELONG", "MANGLE"]

    def __init__(self):
        self.model = AtlasStampClassifier()
        super().__init__("atlas_stamp_classifier", "1.0.0")

    @staticmethod
    def _extract_ra_dec(header: dict) -> Tuple[float, float]:
        """Extracts right ascension and declination of the image center based on FITS header.

        This is the center of the overall image, not necessarily the center of the stamp.

        Due to the non-standard header used in ATLAS, the header itself has to be modified within
        this function and the world celestial coordinate (WCS) transformer is also manipulated in turn.
        These custom conversions have been verified against real ATLAS data.

        Args:
            header (dict): FITS header of ATLAS image

        Returns:
            tuple[float, float]: Right ascension and declination of the center of the field (in degrees)
        """
        header["CTYPE1"] += "-SIP"
        header["CTYPE2"] += "-SIP"
        header["RADESYSa"] = header["RADECSYS"]

        del_fields = [
            "CNPIX1",
            "CNPIX2",
            "RADECSYS",
            "RADESYS",
            "RP_SCHIN",
            "CDANAM",
            "CDSKEW",
        ]
        for field in del_fields:
            if field in header.keys():
                del header[field]

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", AstropyWarning)
            w = WCS(header, relax=True)
        w.sip = None

        pv = []

        for i in [1, 2]:
            for j in range(30):
                pv_name = "PV" + str(i) + "_" + str(j)
                if pv_name in header.keys():
                    pv_val = (i, j, header[pv_name])
                    pv.append(pv_val)

        w.wcs.set_pv(pv)

        w.wcs.ctype = ["RA---TPV", "DEC--TPV"]

        x, y = header["NAXIS1"] * 0.5 + 0.5, header["NAXIS2"] * 0.5 + 0.5
        return w.wcs_pix2world(x, y, 1)

    def extract_image_from_fits(self, stamp_byte: bytes, with_metadata: bool = False):
        """Extracts image from file as a bytes object.

        If metadata is requested, it will include fields defined in `HEADER_FIELDS` as well as the central
        right ascension and declination of the original image.

        Args:
            stamp_byte (bytes): GZipped FITS file as a bytes object
            with_metadata (bool): Whether to include metadata in output

        Returns:
            np.ndarray or tuple[np.ndarray, list]: Image as an array and (optionally) metadata as a list
        """
        with gzip.open(io.BytesIO(stamp_byte), "rb") as fh:
            with fits.open(
                io.BytesIO(fh.read()), memmap=False, ignore_missing_simple=True
            ) as hdu:
                im = hdu[0].data
                header = hdu[0].header
        if not with_metadata:
            return im
        metadata = []
        for field in self.HEADER_FIELDS:
            metadata.append(header[field])

        metadata.extend(self._extract_ra_dec(header))
        return im, metadata

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """Call the prediction method of the model.

        Args:
            df (pd.DataFrame): Data generated by `_to_dataframe`

        Returns:
            pd.DataFrame: Class probabilities. Its columns should be the classifier's classes, and indexed by AID
        """
        return self.model.predict_probs(df)

    def _to_dataframe(self, messages: List[dict]) -> pd.DataFrame:
        """Generate input data frame for model predictor. The output is sorted by date.

        The returned data frame includes all the columns defined in `FIELDS`, taken directly from the
        corresponding field in the alert. Will raise an error if any of these fields are missing from the alert.

        Additionally, it will include the following columns:

        * `red`: Science image (extracted from alert field `science` within `stamps`) as an array,
        * `diff`: Difference image (extracted from alert field `difference` within `stamps`) as an array,

        and all fields from the header in the science image defined in `HEADER_FIELDS` alongside the central
        right ascension and declination of the original image center.

        Args:
            messages (list[dict]): List of messages containing alert data

        Returns:
            pd.DataFrame: Data frame used by the model predictor, indexed by ID
        """
        data, index = [], []
        for msg in messages:
            fields = [msg[field] for field in self.FIELDS]
            science, metadata = self.extract_image_from_fits(
                msg["stamps"]["science"], with_metadata=True
            )
            difference = self.extract_image_from_fits(
                msg["stamps"]["difference"], with_metadata=False
            )
            data.append(fields + [science, difference] + metadata)

            index.append(msg["aid"])

        return pd.DataFrame(
            data=data,
            index=index,
            columns=self.FIELDS + ["red", "diff"] + self.HEADER_FIELDS + ["ra", "dec"],
        ).sort_values("mjd", ascending=True)
