from mamba import describe, context, it
from expects import expect, equal, be_false
from doublex import Spy

from infsnmp.traps import PySnmpTrapDispatcher
from specs import helpers


with describe('Ensure ans1 version Spec'):
    with context('having ans1 version 0.1.2'):

        with context('decoding request_pdu'):
            with it('have prettyPrint method'):

                an_str_oid = '1.3.6.1.6.3.1.1.4.1.0'
                an_oid = helpers.build_oid_object_from(an_str_oid)

                expect(hasattr(an_oid, 'prettyPrint')).to_not(be_false)
