

#include "anal.hh"
struct particle
{
    int N, Z;
    double px, py, pz;
};
class Histograms
{
public:
    Histograms(const std::string &suffix);
    ~Histograms() { ; }
    void fill(const particle &particle, const double betacms, const double &beam_rapidity, const double &weight);
    // void fill(const Event &event, const double betacms, const double &beam_rapidity, const double &weight);
    void normalize(const double &scale);
    void write();

    std::map<std::string, TH2D *> h2_pta_rapidity_lab;

protected:
    std::vector<std::string> PARTICLENAMES = {
        "n", "p", "d", "t", "3He", "4He", "coal_n", "coal_p"};
};

int main(int argc, char *argv[])
{
    // passe args
    std::string reaction = argv[1];
    std::string output_pth = argv[2];

    int nfiles_input = std::stoi(argv[3]);
    std::vector<std::string> input_pths21;
    std::vector<std::string> input_pths3;
    int narg = 4;
    for (int _ = 0; _ < nfiles_input; _++)
    {
        input_pths21.push_back(argv[narg]);
        narg++;
    }
    for (int _ = 0; _ < nfiles_input; _++)
    {
        input_pths3.push_back(argv[narg]);
        narg++;
    }

    // initialize Tchains and other structures
    TChain *chain21 = new TChain("amd");
    TChain *chain3 = new TChain("amd");
    Initialize_TChain(chain21, input_pths21, "filtered", "21");
    Initialize_TChain(chain3, input_pths3, "filtered", "3");

    // initialize Histogramss in different mode
    Histograms *histo21 = new Histograms("primary");
    Histograms *histo3 = new Histograms("secondary");
    Histograms *histo3_one_decay = new Histograms("secondary_one_decay");

    // define physics quantities
    double betacms = Physics::GetReactionBeta(reaction);
    double beam_rapidity = Physics::GetBeamRapidity(reaction);
    int nevents21 = chain21->GetEntries();
    int nevents3 = chain3->GetEntries();

    // counter of weights of each primary event
    std::vector<double> weights(nevents21, 0.);
    double norm_table3 = 0.;
    double norm_table3_one_decay = 0.;
    double norm_table21 = 0.;

    // start filling histogram for table3
    auto start3 = std::chrono::steady_clock::now();
    for (int ievt3 = 0; ievt3 < nevents3; ievt3++)
    {
        chain3->GetEntry(ievt3);

        if (amd.Nc >= 1)
        {
            norm_table3 += 1. / NDECAYS;
            if (ievt3 < nevents3 / NDECAYS)
            {
                norm_table3_one_decay += 1.;
            }
        }
        else
        {
            continue;
        }
        weights[ievt3 % nevents21] += 1.;

        for (int i = 0; i < amd.multi; i++)
        {
            particle particle = {amd.N[i], amd.Z[i], amd.px[i], amd.py[i], amd.pz[i]};

            if (ievt3 < nevents3 / NDECAYS)
            {
                histo3_one_decay->fill(particle, betacms, beam_rapidity, 1.);
            }
            histo3->fill(particle, betacms, beam_rapidity, 1. / NDECAYS);
        }
    }
    auto end3 = std::chrono::steady_clock::now();
    std::chrono::duration<double> timer3 = end3 - start3;

    // filling Histograms for table21
    auto start21 = std::chrono::steady_clock::now();
    for (int ievt21 = 0; ievt21 < nevents21; ievt21++)
    {
        chain21->GetEntry(ievt21);
        weights[ievt21] /= 1.0 * NDECAYS;

        for (unsigned int i = 0; i < amd.multi; i++)
        {
            double A = amd.N[i] + amd.Z[i];
            particle particle = {amd.N[i], amd.Z[i], amd.px[i] * A, amd.py[i] * A, amd.pz[i] * A};
            histo21->fill(particle, betacms, beam_rapidity, weights[ievt21]);
        }

        norm_table21 += weights[ievt21];
    }
    auto end21 = std::chrono::steady_clock::now();
    std::chrono::duration<double> timer21 = end21 - start21;

    // replacing table3 errorbars by table3-one-decay
    for (auto &[pn, h2] : histo3->h2_pta_rapidity_lab)
    {
        for (int i = 0; i < h2->GetNbinsX(); i++)
        {
            for (int j = 0; j < h2->GetNbinsY(); j++)
            {
                double error = histo3_one_decay->h2_pta_rapidity_lab[pn]->GetBinError(i + 1, j + 1);
                h2->SetBinError(i + 1, j + 1, error);
            }
        }
    }

    // saving results
    TFile *outputfile = new TFile(output_pth.c_str(), "RECREATE");
    outputfile->cd();
    histo21->normalize(norm_table21);
    histo3->normalize(norm_table3);
    histo3_one_decay->normalize(norm_table3_one_decay);
    histo21->write();
    histo3->write();
    histo3_one_decay->write();
    outputfile->Write();
    std::cout << "Elapsed Time reading table3 : " << timer3.count() << std::endl;
    std::cout << "Elapsed Time reading table21 : " << timer21.count() << std::endl;
}

Histograms::Histograms(const std::string &suffix)
{
    for (const auto &pn : this->PARTICLENAMES)
    {
        std::string hname = Form("h2_pt_rapidity_%s_%s", suffix.c_str(), pn.c_str());
        this->h2_pta_rapidity_lab[pn] = new TH2D(hname.c_str(), "", 100, 0., 1., 600, 0, 600);
        this->h2_pta_rapidity_lab[pn]->Sumw2();
        this->h2_pta_rapidity_lab[pn]->SetDirectory(0);
    }
}

void Histograms::fill(const particle &particle, const double betacms, const double &beam_rapidity, const double &weight)
{
    std::string name = Physics::GetNucleiName(particle.Z, particle.Z + particle.N);

    double pt = Physics::GetPt(particle.px, particle.py);
    double p = Physics::GetP(pt, particle.pz);
    double mass = Physics::GetNucleiMass(particle.Z, particle.Z + particle.N);
    double kinergy = Physics::GetEkin(mass, p);
    double rapidity_cms = Physics::GetRapidity(kinergy, particle.pz, mass);

    double pz_lab = Physics::boostz(mass, particle.pz, kinergy, -betacms);
    double p_lab = Physics::GetP(pt, pz_lab);
    double kinergy_lab = Physics::GetEkin(mass, p_lab);
    double rapidity_lab = Physics::GetRapidity(kinergy_lab, pz_lab, mass);

    double rapidity_lab_normed = rapidity_lab / beam_rapidity;

    if (this->h2_pta_rapidity_lab.count(name) == 1)
    {
        this->h2_pta_rapidity_lab[name]->Fill(rapidity_lab_normed, pt, weight);
    }

    if (this->h2_pta_rapidity_lab.count("coal_p") == 1)
    {
        this->h2_pta_rapidity_lab["coal_p"]->Fill(rapidity_lab_normed, pt, weight * particle.Z);
    }
    if (h2_pta_rapidity_lab.count("coal_n") == 1)
    {
        this->h2_pta_rapidity_lab["coal_n"]->Fill(rapidity_lab_normed, pt, weight * particle.N);
    }
    return;
}

void Histograms::write()
{
    for (const auto &pn : this->PARTICLENAMES)
    {
        this->h2_pta_rapidity_lab[pn]->Write();
    }
}

void Histograms::normalize(const double &scale)
{
    for (const auto &pn : this->PARTICLENAMES)
    {
        this->h2_pta_rapidity_lab[pn]->Scale(1. / scale);
    }
}
