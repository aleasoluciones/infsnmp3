from mamba import description, context, it, before
from expects import expect, equal, contain, raise_error

from infsnmp import oid_converter, exceptions


with description('PyOIDConverter') as self:
    with before.each:
        self.converter = oid_converter.PyOIDConverter('', ['IP-MIB'])

    with context('FEATURE: converting oid to symbol'):
        with context('happy path'):
            with it('returns the symbol'):

                mib_symbol = self.converter.to_symbol('1.3.6.1.2.1.4.20.1.4.192.168.112.1')

                expect(mib_symbol.symbol).to(equal('ipAdEntBcastAddr'))
                expect(mib_symbol.base_oid).to(equal('1.3.6.1.2.1.4.20.1.4'))
                expect(mib_symbol.node_suffixes).to(contain('192', '168', '112', '1'))

        with context('having an invalid oid'):
            with it('raises exception'):

                def _convert_invalid_oid():
                    self.converter.to_symbol('9')

                expect(_convert_invalid_oid).to(raise_error(exceptions.InvalidOIDError))
