#ifndef Particle_hh
#define Particle_hh

#include "TMath.h"
#include "Physics.hh"

class Particle
{
public:
    Particle(const int &N, const int &Z, const double &px_per_nucleon, const double &py_per_nucleon, const double &pz_cms_per_nucleon, const double &m = 0.);
    ~Particle() { ; }

    void Initialize(const double &betacms);

    int N, Z, A;
    double mass;

    // same in lab and cms
    double px, py, phi, pmag_trans;

    // cms quantities
    double pz_cms;
    double theta_cms, kinergy_cms, pmag_cms, rapidity_cms;

    // lab quantities
    double pz_lab;
    double theta_lab, kinergy_lab, pmag_lab, rapidity_lab;

protected:
    double NucleonMass = 938.272; // MeV/c^2
};
#endif