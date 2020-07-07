from django.db import models

from project.mixins import UUIDModel


class Currency(UUIDModel):
    name = models.CharField(max_length=32)

    # TODO: additional fields?
    def __str__(self):
        return self.name



# class VerificationInput(CurrencyOwnedMixin):
#     # label =  charfield max_length=32  (i18n)
#     # type : text / boolean / number / date  (-> integerfield choices)
    
#     # name adress DOB  checkbox telling truth
#     # app creates ui with this
#     # BE has to verify data

#     # -> Set to verified if ok (on post request); cannot claim until verified

#     pass