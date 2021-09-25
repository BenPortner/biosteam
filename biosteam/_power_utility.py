# -*- coding: utf-8 -*-
# BioSTEAM: The Biorefinery Simulation and Techno-Economic Analysis Modules
# Copyright (C) 2020-2021, Yoel Cortes-Pena <yoelcortes@gmail.com>
# 
# This module is under the UIUC open-source license. See 
# github.com/BioSTEAMDevelopmentGroup/biosteam/blob/master/LICENSE.txt
# for license details.
"""
"""
from thermosteam.units_of_measure import DisplayUnits, convert

__all__ = ('PowerUtility',)


default_price = 0.0782
default_GWPCF = 0.48
default_FECCF = 5.926

class PowerUtility:
    """
    Create an PowerUtility object that stores data on consumption and production
    of electricity.
            
    Notes
    -----
    The default price is 0.0782 USD/kWhr as suggested in [1]_.
    The default GWP and FEC characterization factors are 0.48 kg CO2-eq / kWhr
    and 5.926 MJ / kWhr, as suggested in [2]_.
    
    References
    ----------
    [1] Seider, W. D., Lewin,  D. R., Seader, J. D., Widagdo, S., Gani, R.,
        & Ng, M. K. (2017). Product and Process Design Principles. Wiley.
    [2] Argonne National Laboratory. The Greenhouse gases, Regulated Emissions,
    and Energy use in Transportation (GREET) Model https://greet.es.anl.gov/
    (accessed Aug 25, 2020).
    
    Examples
    --------
    Create a PowerUtility object:
    
    >>> pu = PowerUtility()
    >>> pu
    PowerUtility(consumption=0.0, production=0.0)
    
    PowerUtility objects have `consumption` and `production` attributes
    which are updated when setting the rate with the assumption that
    a positive rate means no production (only consumption) and a negative
    rate means no consumption (only consumption).
    
    >>> pu(rate=-500)
    >>> pu.consumption, pu.production
    (0.0, 500.0)
    
    >>> pu(rate=500.)
    >>> pu.consumption, pu.production
    (500.0, 0.0)
    
    It is possible to have both consumption and production by setting these
    attributes individually (instead of setting rate)
    
    >>> pu.production = 100. 
    >>> pu.rate
    400.0
    
    Notice how the rate is equal to the consumption minus the production.
    
    The cost is available as a property:
    
    >>> pu.cost # USD/hr
    31.28
    
    It may be useful to print results in different units of measure:
    
    >>> pu.show(rate='BTU/s')
    PowerUtility:
     consumption: 474 BTU/s
     production: 94.8 BTU/s
     rate: -379 BTU/s
     cost: 31.3 USD/hr
    
    """
    __slots__ = ('consumption', 'production')
    
    #: [DisplayUnits] Units of measure for IPython display
    display_units = DisplayUnits(rate='kW', cost='USD/hr')
    
    def __init__(self, consumption=0., production=0.):
        #: Electricity consumption [kW]
        self.consumption = consumption
        
        #: Electricity production [kW]
        self.production = production
    
    @classmethod
    def default_price(cls):
        """Reset price back to BioSTEAM's default."""
        cls.price = default_price #: [float] USD/kWhr
    
    @classmethod
    def default_GWPCF(cls):
        """Reset the global warming potential characterization factor 
        back to BioSTEAM's default."""
        cls.GWPCF = default_GWPCF #: [float] kg CO2-eq/kWh
    
    @classmethod
    def default_FECCF(cls):
        """Reset the fossil energy consumption characterization factor 
        back to BioSTEAM's default."""
        cls.FECCF = default_FECCF #: [float] MJ/kWh
    
    @property
    def GWP(self):
        """Return the global warming potential in kg CO2-eq / hr given the 
        method name."""
        return (self.consumption - self.production) * self.GWPCF
    
    @property
    def FEC(self):
        """Return the fossil energy consumption in MJ/hr given the method name."""
        return (self.consumption - self.production) * self.FECCF
    
    @property
    def rate(self):
        """Power requirement [kW]."""
        return self.consumption - self.production
    @rate.setter
    def rate(self, rate):
        rate = float(rate)
        if rate >= 0.:
            self.consumption = rate
            self.production = 0.
        else:
            self.consumption = 0.
            self.production = -rate
    
    @property
    def cost(self):
        """Cost [USD/hr]"""
        return self.price * self.rate
    
    def __bool__(self):
        return bool(self.consumption or self.production)
    
    def __call__(self, rate):
        """Set rate in kW."""
        self.rate = rate
    
    def copy(self):
        return self.__class__(self.consumption, self.production)
    
    def mix_from(self, power_utilities):
        """
        Mix in requirements of power utilities.
        
        Examples
        --------
        >>> pus = [PowerUtility(production=100),
        ...        PowerUtility(consumption=50),
        ...        PowerUtility(production=20)]
        >>> pu = PowerUtility()
        >>> pu.mix_from(pus)
        >>> pu
        PowerUtility(consumption=50.0, production=120.0)
        
        """
        self.consumption = sum([i.consumption for i in power_utilities])
        self.production = sum([i.production for i in power_utilities])
    
    def copy_like(self, power_utility):
        """Copy consumption anf production rates from another power utility."""
        self.consumption = power_utility.consumption
        self.production = power_utility.production
    
    def scale(self, scale):
        """Scale consumption and production accordingly."""
        self.consumption *= scale
        self.production *= scale
    
    @classmethod
    def sum(cls, power_utilities):
        """
        Return a PowerUtility object that represents the sum of power utilities.
        
        Examples
        --------
        >>> pus = [PowerUtility(production=100),
        ...        PowerUtility(consumption=50),
        ...        PowerUtility(production=20)]
        >>> pu = PowerUtility.sum(pus)
        >>> pu
        PowerUtility(consumption=50.0, production=120.0)
        
        """
        power_utility = cls()
        power_utility.mix_from(power_utilities)
        return power_utility
    
    def show(self, rate=None, cost=None):
        # Get units of measure
        display_units = self.display_units
        rate_units = rate or display_units.rate
        cost_units = cost or display_units.cost
        production = convert(self.production, 'kW', rate_units)
        consumption = convert(self.consumption, 'kW', rate_units)
        rate = production - consumption
        cost = convert(self.cost, 'USD/hr', cost_units)
        print(f'{type(self).__name__}:\n'
              f' consumption: {consumption:.3g} {rate_units}\n'
              f' production: {production:.3g} {rate_units}\n'
              f' rate: {rate:.3g} {rate_units}\n'
              f' cost: {cost:.3g} {cost_units}')
    _ipython_display_ = show    
    
    def __repr__(self):
        return f'{type(self).__name__}(consumption={self.consumption}, production={self.production})'
    
PowerUtility.default_price()
PowerUtility.default_GWPCF()