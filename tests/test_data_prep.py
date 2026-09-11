from src.data_prep import clean_text, looks_english


def test_customer_text_cleaning():
    raw = "@115888: @SpotifyCares my songs vanished https://t.co/abc123 &amp; @441 too"
    assert clean_text(raw) == "my songs vanished [link] & @user too"


def test_brand_signature_and_part_markers_removed():
    assert clean_text("@123 Hey! Try logging out &gt; back in /JN https://t.co/x", is_brand=True) \
        == "Hey! Try logging out > back in [link]"
    assert clean_text("1: We're on it, stay tuned ^Kev", is_brand=True) == "We're on it, stay tuned"
    assert clean_text("Can you DM us your email... (1/2)", is_brand=True) == "Can you DM us your email..."


def test_brand_text_keeps_normal_words():
    assert clean_text("Go to Settings and toggle Crossfade", is_brand=True) == \
        "Go to Settings and toggle Crossfade"


def test_looks_english():
    assert looks_english("why is my playlist gone?")
    assert looks_english("ok thanks")
    assert looks_english("I’m having issue being verified as a student.")
    assert looks_english("Still no words about releasing Spotify in India. :(")
    assert not looks_english("net een premium account omgezet. Hoe kan ik mijn dochter toevoegen?")
    assert not looks_english("me han cobrado dos veces necesito ayuda por favor")
    assert not looks_english("ありがとうございます、助かりました")
    assert not looks_english("😭😭😭")
