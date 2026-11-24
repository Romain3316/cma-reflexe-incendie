import io
import json
import unittest
from pathlib import Path
from calculator import calculate
from pdf_export import make_pdf
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).parent

class Catalogue2027Tests(unittest.TestCase):
    def setUp(self):
        self.courses=json.loads((ROOT/'formations_2027.json').read_text())['courses']

    def test_official_selection_and_missing_data(self):
        self.assertEqual(len(self.courses),80)
        self.assertEqual({x['official_row'] for x in self.courses},set(range(4,84)))
        self.assertFalse(any('LinkedIn' in x['title'] for x in self.courses))
        self.assertTrue(next(x for x in self.courses if x['official_row']==25)['condition'])
        self.assertIsNone(next(x for x in self.courses if x['official_row']==13)['days'])

    def test_unknown_duration_and_cpf_gate(self):
        at=AppTest.from_file(str(ROOT/'app.py')).run(timeout=30)
        self.assertFalse(at.exception)
        self.assertNotIn('Contact professionnel',[x.label for x in at.text_input])
        next(x for x in at.number_input if x.label=='Nombre de formations prévues').set_value(1).run()
        next(x for x in at.selectbox if x.label=='Formation').select('Développer la Vente à emporter avec un service de qualité').run()
        next(x for x in at.checkbox if x.label.startswith('J’ai vérifié')).check().run()
        next(x for x in at.checkbox if x.label=='Formation éligible et financement vérifiés').check().run()
        self.assertTrue(at.get('download_button')[0].disabled)
        next(x for x in at.number_input if x.label.startswith('Durée confirmée')).set_value(2.0).run()
        self.assertTrue(at.get('download_button')[0].disabled)
        next(x for x in at.checkbox if x.label.startswith('Durée vérifiée')).check().run()
        next(x for x in at.number_input if x.label.startswith('Reste à charge')).set_value(70.0).run()
        self.assertFalse(at.exception)
        self.assertFalse(at.get('download_button')[0].disabled)
        next(x for x in at.checkbox if x.label=='Cette formation est financée par le CPF').check().run()
        self.assertTrue(at.get('download_button')[0].disabled)
        self.assertTrue(any('non appliquée' in x.value for x in at.warning))

    def test_pdf_training_links_and_fixed_contact(self):
        from pypdf import PdfReader
        tva=next(x for x in self.courses if x['title']=='Gérer ma TVA')
        data=make_pdf(calculate([],hours=2,days=1,rac=70,eligible=True),'Test & <Entreprise>','Micro','Romain','old@example.com','TTC',[],trainings=[tva])
        reader=PdfReader(io.BytesIO(data));text='\n'.join(p.extract_text() for p in reader.pages)
        self.assertIn('3006',text);self.assertNotIn('old@example.com',text)
        self.assertIn(tva['summary'],text.replace('\n',' '))
        self.assertIn('VOS FORMALITÉS',text)
        self.assertIn('VOTRE CONSEIL SUR MESURE',text)
        links=[a.get_object().get('/A',{}).get('/URI') for p in reader.pages for a in p.get('/Annots',[])]
        self.assertIn(tva['source_url'],links)

if __name__=='__main__':unittest.main()
