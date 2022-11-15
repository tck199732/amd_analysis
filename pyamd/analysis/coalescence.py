import pandas as pd
import numpy as np
import itertools
from pyamd.utilities import helper
df_helper = helper.DataFrameHelper()


class Coalescence:
    def __init__(self, reaction, skyrme='SkM', Nc=(11, 25), bimp=(0., 3.)):
        self.reaction = reaction
        self.skyrme = skyrme
        self.Nc = Nc
        self.bimp = bimp
        self.spectra = dict()

    def add_spectra(self, particle, df):
        self.spectra[particle] = df

    def pseudo_neutron(self, bins=30, range=(0, 600)):

        required_particle = ['p', 't', '3He']
        if not (set(required_particle).issubset(self.spectra)):
            raise ValueError(f'require {required_particle} spectra for pseudo neutron.')

        df = dict()
        for pn in required_particle:
            df[pn] = df_helper.rebin1d(
                self.spectra[pn], bins=bins, range=range)
        df['p*t'] = df_helper.product1d(df['p'], df['t'])
        return df_helper.ratio1d(df['3He'], df['p*t'])

    def npRatio(self, range=(0, 600), bins=30, pseudo_neutron=False):
        if not 'p' in self.spectra:
            raise ValueError('proton spectrum is absent.')

        if not 'n' in self.spectra and not pseudo_neutron:
            raise ValueError('No neutron spectra.')

        if pseudo_neutron:
            df1 = self.pseudo_neutron(range=range, bins=bins)
        else:
            df1 = self.spectra['n'].copy()

        df1 = helper.rebin1d(df1, range=range, bins=bins)
        df2 = helper.rebin1d(self.spectra['p'], range=range, bins=bins)
        return helper.ratio1d(df2, df1)

    def plot_npRatio(self, ax=None, range=(0, 600), bins=30, pseudo_neutron=False, **kwargs):
        df = self.npRatio(range=range, bins=bins,
                          pseudo_neutron=pseudo_neutron)
        return helper.plot1d(ax, df, drop_zeros=True, drop_large_err=True, rel_err=0.05, **kwargs)

    def ChemicalTemperature(self, bins=30, range=(0, 600)):

        required_particle = ['d', '4He', 't', '3He']
        if not (set(required_particle).issubset(self.spectra)):
            raise ValueError(
                'require d, 4He, t, 3He spectra for calculating chemical temperature.')

        df = dict()
        for pn in required_particle:
            df[pn] = helper.rebin1d(self.spectra[pn], range=range, bins=bins)

        num = df['d']['y'] * df['4He']['y']
        den = df['t']['y'] * df['3He']['y']

        T = np.divide(num, den, where=(
            (num != 0.0) & (den != 0.0)), out=np.zeros_like(num))
        err = T * np.sqrt(df['d']['y_ferr']**2 + df['4He']['y_ferr']
                          ** 2 + df['t']['y_ferr']**2 + df['3He']['y_ferr']**2)
        err = err / np.log(T, where=(T > 0.0))**2

        T, err = (
            14.3 / np.log(T, where=(T > 0.0)),
            14.3 * np.divide(err, T, out=np.zeros_like(err), where=(T > 0.0))
        )

        T, bin_edges = np.histogram(
            df['d']['x'], bins=bins, range=range, weights=T)
        err, bin_edges = np.histogram(
            df['d']['x'], bins=bins, range=range, weights=err**2)
        err = np.sqrt(err)

        x_edges = np.linspace(*range, bins+1)
        return pd.DataFrame({
            'x': 0.5 * (x_edges[1:] + x_edges[:-1]),
            'y': T,
            'y_err': err,
            'y_ferr': np.divide(err, T, out=np.zeros_like(err), where=(T > 0.0))
        })

    def coalescence_neutron(self, range=(0, 600), bins=30, pseudo_neutron=True):
        df = dict()
        for pn in self.spectra:
            df[pn] = df_helper.rebin1d(
                self.spectra[pn], range=range, bins=bins)

        if pseudo_neutron:
            df['n'] = self.pseudo_neutron(bins=bins, range=range)

        edges = np.linspace(*range, bins+1)
        y = df['n'].y + df['d'].y + 2.*df['t'].y + df['3He'].y + 2.*df['4He'].y
        yerr = np.sqrt(
            df['n']['y_err']**2 + 
            df['d']['y_err']**2 + 
            4. *df['t']['y_err']**2 + 
            df['3He']['y_err']**2 +
            4. * df['4He']['y_err']**2
        )

        return pd.DataFrame({
            'x': 0.5 * (edges[1:]+edges[:-1]),
            'y': y,
            'y_err': yerr,
            'y_ferr': np.divide(yerr, y, where=(y != 0.0), out=np.zeros_like(yerr))
        })

    def coalescence_proton(self, range=(0, 600), bins=30):
        df = dict()
        for pn in self.spectra:
            df[pn] = df_helper.rebin1d(
                self.spectra[pn], range=range, bins=bins)

        edges = np.linspace(*range, bins+1)
        y = df['p'].y + df['d'].y + df['t'].y + 2.*df['3He'].y + 2.*df['4He'].y
        yerr = np.sqrt(
            df['p']['y_err']**2 + 
            df['d']['y_err']**2 + 
            df['t']['y_err']** 2 + 
            4. * df['3He']['y_err']**2 + 
            4. * df['4He']['y_err']**2
        )

        return pd.DataFrame({
            'x': 0.5 * (edges[1:]+edges[:-1]),
            'y': y,
            'y_err': yerr,
            'y_ferr': np.divide(yerr, y, where=(y != 0.0), out=np.zeros_like(yerr))
        })

    # def coalescence(self, particles=None, coal='p', range=(0, 600), bins=30, pseudo_neutron=True):

    #     if pseudo_neutron:
    #         if 'n' in self.spectra:
    #             self.spectra.pop('n')
    #         self.spectra['n'] = self.pseudo_neutron(range=range, bins=bins)
    #     if particles is None:
    #         particles = [particle for particle in self.spectra]

    #     spectra = [self.spectra[particle] for particle in particles]
    #     keys = [(e15190.particle(particle).Z, e15190.particle(particle).N)
    #             for particle in particles]

    #     spectra = [helper.rebin1d(df, range=range, bins=bins)
    #                for df in spectra]

    #     df = pd.concat(spectra, keys=keys, names=['Z', 'N'])
    #     if coal == 'p':
    #         y = df.groupby(['x']).apply(
    #             lambda x: np.sum(x.y * x.index.get_level_values('Z').astype(float)))
    #     elif coal == 'n':
    #         y = df.groupby(['x']).apply(
    #             lambda x: np.sum(x.y * x.index.get_level_values('N').astype(float)))

    #     yerr = df.groupby(['x']).apply(
    #         lambda x: np.sum(x['y_err']**2))
    #     yerr = np.sqrt(yerr)

    #     edges = np.linspace(*range, bins+1)
    #     return pd.DataFrame({
    #         'x': 0.5 * (edges[1:]+edges[:-1]),
    #         'y': y,
    #         'y_err': yerr,
    #         'y_ferr': np.divide(yerr, y, where=(y != 0.0), out=np.zeros_like(yerr))
    #     })

    # def coalescence_n(self, df_n=None, df_p=None, df_d=None, df_t=None, df_3He=None, df_4He=None, range=(0, 600), bins=30):
    #     df_n = helper.rebin1d(df_n, range=range, bins=bins)
    #     df_p = helper.rebin1d(df_p, range=range, bins=bins)
    #     df_d = helper.rebin1d(df_d, range=range, bins=bins)
    #     df_t = helper.rebin1d(df_t, range=range, bins=bins)
    #     df_3He = helper.rebin1d(df_3He, range=range, bins=bins)
    #     df_4He = helper.rebin1d(df_4He, range=range, bins=bins)

    #     edges = np.linspace(*range, bins+1)
    #     y = df_n.y + df_d.y + 2.*df_t.y + df_3He.y + 2.*df_4He.y
    #     yerr = np.sqrt(df_n['y_err']**2 + df_d['y_err']**2 + 4. *
    #                    df_t['y_err']**2 + df_3He['y_err']**2 + 4. * df_4He['y_err']**2)

    #     return pd.DataFrame({
    #         'x': 0.5 * (edges[1:]+edges[:-1]),
    #         'y': y,
    #         'y_err': yerr,
    #         'y_ferr': np.divide(yerr, y, where=(y != 0.0), out=np.zeros_like(yerr))
    #     })

    # def coalescence_p(self, df_n=None, df_p=None, df_d=None, df_t=None, df_3He=None, df_4He=None, range=(0, 600), bins=30):
    #     df_n = helper.rebin1d(df_n, range=range, bins=bins)
    #     df_p = helper.rebin1d(df_p, range=range, bins=bins)
    #     df_d = helper.rebin1d(df_d, range=range, bins=bins)
    #     df_t = helper.rebin1d(df_t, range=range, bins=bins)
    #     df_3He = helper.rebin1d(df_3He, range=range, bins=bins)
    #     df_4He = helper.rebin1d(df_4He, range=range, bins=bins)

    #     edges = np.linspace(*range, bins+1)
    #     y = df_p.y + df_d.y + df_t.y + 2. * df_3He.y + 2. * df_4He.y
    #     yerr = np.sqrt(df_p['y_err']**2 + df_d['y_err']**2 + df_t['y_err']
    #                    ** 2 + 4. * df_3He['y_err']**2 + 4. * df_4He['y_err']**2)

    #     return pd.DataFrame({
    #         'x': 0.5 * (edges[1:]+edges[:-1]),
    #         'y': y,
    #         'y_err': yerr,
    #         'y_ferr': np.divide(yerr, y, where=(y != 0.0), out=np.zeros_like(yerr))
    #     })
