import pandas as pd
import numpy as np
import itertools
from typing import Literal

from pyamd.e15190 import e15190
from pyamd.utilities import dataframe
df_helper = dataframe.DataFrameHelper()

class Coalescence:

    @staticmethod
    def pseudo_neutron(proton, triton, helium3, bins=30, range=(0,600)):
        
        proton_spectra = df_helper.rebin1d(proton, bins=bins, range=range)
        triton_spectra = df_helper.rebin1d(triton, bins=bins, range=range)
        helium3_spectra = df_helper.rebin1d(helium3, bins=bins, range=range)
        return df_helper.ratio1d(helium3_spectra, df_helper.multiply(proton_spectra, triton_spectra))

    @staticmethod
    def chemical_temperature(
        deuteron, alpha, triton, helium3,
        bins=30, range=(0, 600)
    ):
        deuteron_spectrum = df_helper.rebin1d(deuteron, bins=bins, range=range)
        alpha_spectrum = df_helper.rebin1d(alpha, bins=bins, range=range)
        triton_spectrum = df_helper.rebin1d(triton, bins=bins, range=range)
        helium3_spectrum = df_helper.rebin1d(helium3, bins=bins, range=range)
        
        x = deuteron_spectrum['x']

        num = deuteron_spectrum['y'] * alpha_spectrum['y']
        den = triton_spectrum['y'] * helium3_spectrum['y']

        val = np.divide(num, den, where=(
            (num != 0.0) & (den != 0.0)), out=np.zeros_like(num))

        err = val * np.sqrt(deuteron_spectrum['y_ferr']**2 + alpha_spectrum['y_ferr']
                          ** 2 + triton_spectrum['y_ferr']**2 + helium3_spectrum['y_ferr']**2)

        T = 14.3 / np.log(1.59 * val, where=(val > 0.))
        T_err = 14.3 * err / val / (np.log(1.59 * val, where=(val>0.))) ** 2.

        return pd.DataFrame({
            'x' : x,
            'y': T,
            'y_err': T_err,
            'y_ferr': np.divide(T_err, T, out=np.zeros_like(T_err), where=(T > 0.0))
        })

    @staticmethod
    def coalescence_spectra(spectra, type:Literal['p','n']='p', range=(0, 600), bins=30):
        """
        spectra : dict
            `key = (Z,N)` 
            `value` = pd.DataFrame
        """

        rebinned_spectra = dict()
        for zn, df in spectra.items():
            rebinned_spectra[zn] = df_helper.rebin1d(df, range=range, bins=bins)
        
        x = np.linspace(*range, bins+1)
        x = 0.5 * (x[1:] + x[:-1])
        
        y = np.sum([
            df['y'] * zn[type == 'n'] for zn, df in rebinned_spectra.items()
        ], axis=0)
        yerr = np.sqrt(np.sum([
            df['y_err'] ** 2 * zn[type == 'n'] ** 2 for zn, df in rebinned_spectra.items()
        ], axis=0))

        return pd.DataFrame({
            'x': x,
            'y': y,
            'y_err': yerr
        })