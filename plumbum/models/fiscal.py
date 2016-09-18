# -*- coding: utf-8 -*-

from plumbum.models import db


class FiscalData(db.Model):
    __tablename__ = 'fiscal_data'

    FISCAL_CONSUMIDOR_FINAL = 'CONSUMIDOR FINAL'
    FISCAL_RESPONSABLE_INSCRIPTO = 'RESPONSABLE INSCRIPTO'
    FISCAL_EXCENTO = 'EXCENTO'
    FISCAL_MONOTRIBUTO = 'MONOTRIBUTO'

    _fiscal_types = (
        FISCAL_CONSUMIDOR_FINAL,
        FISCAL_RESPONSABLE_INSCRIPTO,
        FISCAL_EXCENTO,
        FISCAL_MONOTRIBUTO,
    )

    id = db.Column(db.Integer, primary_key=True)
    cuit = db.Column(db.Unicode(13))
    fiscal_type = db.Column(db.Enum(*_fiscal_types, name='fiscal_type_enum'),
                            default=FISCAL_CONSUMIDOR_FINAL)

    @property
    def needs_cuit(self):
        return self.fiscal_type not in (self.FISCAL_CONSUMIDOR_FINAL,)


    def __repr__(self):
        return "<FiscalData '{} {}' of '{}'>".format(
            self.fiscal_type,
            self.cuit,
            self.entity.full_name
        )

# TODO: Fetch for AFIP data based on CUIT
