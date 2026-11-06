import unittest
from decimal import Decimal
from calculator import calculate
from pdf_export import make_pdf
class CalculationTests(unittest.TestCase):
 def test_micro(self):
  r=calculate([dict(label='Adresse',ht=58.33,covered=True)],days=4,rac=70,eligible=True,cap=70)
  self.assertEqual(r['gain'],Decimal('-8.56'))
 def test_advice(self):
  r=calculate([],hours=3,basis='HT');self.assertEqual(r['rows'][0][1:],(Decimal('237'),Decimal('79')))
 def test_limits(self):
  r=calculate([],days=4,rac=20,eligible=True,cap=70);self.assertEqual(r['rows'][1][2],0)
  self.assertEqual(calculate([],days=4,rac=20,eligible=False,cap=70)['rows'][1][2],80)
  with self.assertRaises(ValueError):calculate([dict(label='x',ht=30,covered=True)]*3)
 def test_free(self):self.assertEqual(calculate([],free=True)['subscription'],Decimal('298.80'))
 def test_pdf(self):
  self.assertTrue(make_pdf(calculate([]),'Test <Entreprise>','Micro','Conseiller','contact','TTC',['Test']).startswith(b'%PDF'))
if __name__=='__main__':unittest.main()
