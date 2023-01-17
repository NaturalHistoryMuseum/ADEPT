import unittest


from adept.pipeline import Pipeline
from adept.config import RAW_DATA_DIR


class FieldsTest(unittest.TestCase):
    
    def setUp(self):
        self.pipeline = Pipeline()

    def test_pipeline(self):  
        tpl_path = RAW_DATA_DIR / 'fields.tpl.yml'
        text = """Perennial 40-100 cm tall. Culms slender to moderately robust, erect or decumbent and rooting at lower nodes, up to 80 cm tall, nodes glabrous, eglandular or with glandular ring. Leaf sheaths shorter than internodes, glabrous except for ciliate outer margin; leaf blades narrowly lanceolate, 3–10 × 0.4–0.8 cm, glabrous, scabrid, base rounded, apex acute; ligule 1–2 mm. Panicle open, ovate in outline, 4–11 cm, glandular, many-spiculate; branches and pedicels filiform, flexuose; pedicels variable in length, shorter or longer than spikelets. Spikelets elliptic-globose, 1.5–2(–2.2) mm, greenish or purplish brown; florets slightly to clearly dissimilar; lower floret male, upper floret female; glumes subequal, as long as or shorter than florets, broadly elliptic, 5–7(–9)-veined, usually glabrous, rarely hispidulous or scaberulous above middle, apex broadly rounded; lower lemma oblong, cartilaginous to subcrustaceous, shallowly convex, back sometimes sulcate, smooth, glabrous; anthers 0.8–1.3 mm; upper lemma crustaceous, shorter and more convex, slightly rough, back glabrous or puberulous, upper margins ciliate. Fl. and fr. summer to autumn. 2n = 60.
        Wet places, forming colonies, and as a weed of rice fields. Anhui, Fujian, Guangdong, Guangxi, Guizhou, Hebei, Henan, Hubei, Hunan, Jiangsu, Jiangxi, Liaoning, Shaanxi, Shandong, Taiwan, Yunnan, Zhejiang [Bangladesh, Bhutan, India, Indonesia, Japan, Korea, Malaysia, Nepal, New Guinea, Philippines, Sri Lanka, Thailand, Vietnam; Australia, Pacific Islands].
        This is a widespread and very variable species. 2 ovaries. 56 stamenoids. Seed volume is about 2 cm³. It includes several ill-defined entities that have been given specific rank in the past. The typical form, from Japan, has spikelets with the florets only slightly dissimilar, nearly equal in length and texture and the upper floret rounded on the back without a central groove. This form is the most common entity in China. Specimens from India usually have more clearly unequal florets, the lower one longer and thinner, with a deep, longitudinal groove on the back. This form may have a glabrous or pubescent upper floret, and the pubescent variant is the basis of the name Isachne mili-acea. In SE Asia this division breaks down, with many intermediate forms. Specimens in which the florets are nearly equal but the lower one is grooved also occur in China. There is much variation in habit and spikelet size unrelated to other characters.
        """

        fields = self.pipeline(text, 'angiosperm')
        
        
        print(fields.to_template(tpl_path))
        
        




if __name__ == '__main__':
    unittest.main()
