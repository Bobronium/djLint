"""Djlint tests specific to django.

run::

   pytest tests/test_django.py --cov=src/djlint --cov-branch \
          --cov-report xml:coverage.xml --cov-report term-missing

for a single test, run::

   pytest tests/test_django.py::test_comment --cov=src/djlint \
     --cov-branch --cov-report xml:coverage.xml --cov-report term-missing

"""
# pylint: disable=C0116

from typing import TextIO

from click.testing import CliRunner

from .conftest import reformat


def test_empty_tags_on_one_line(runner: CliRunner, tmp_file: TextIO) -> None:
    output = reformat(tmp_file, runner, b"{% if stuff %}\n{% endif %}")
    assert output.text == """{% if stuff %}{% endif %}\n"""
    assert output.exit_code == 1


def test_dj_comments_tag(runner: CliRunner, tmp_file: TextIO) -> None:
    output = reformat(
        tmp_file, runner, b"{# comment #}\n{% if this %}<div></div>{% endif %}"
    )
    assert output.text == """{# comment #}\n{% if this %}<div></div>{% endif %}\n"""
    # no change was required
    assert output.exit_code == 0


def test_reformat_asset_tag(runner: CliRunner, tmp_file: TextIO) -> None:
    # pylint: disable=C0301
    output = reformat(
        tmp_file,
        runner,
        b"""{% block css %}{% assets "css_error" %}<link type="text/css" rel="stylesheet" href="{{ ASSET_URL }}" />{% endassets %}{% endblock css %}""",
    )  # noqa: E501
    assert (
        output.text
        == """{% block css %}
    {% assets "css_error" %}
        <link type="text/css" rel="stylesheet" href="{{ ASSET_URL }}" />
    {% endassets %}
{% endblock css %}
"""
    )
    assert output.exit_code == 1


def test_autoescape(runner: CliRunner, tmp_file: TextIO) -> None:
    output = reformat(
        tmp_file, runner, b"{% autoescape on %}{{ body }}{% endautoescape %}"
    )
    assert output.exit_code == 1
    assert (
        output.text
        == r"""{% autoescape on %}
    {{ body }}
{% endautoescape %}
"""
    )


def test_comment(runner: CliRunner, tmp_file: TextIO) -> None:
    output = reformat(
        tmp_file, runner, b"""{% comment "Optional note" %}{{ body }}{% endcomment %}"""
    )
    assert output.exit_code == 0
    # too short to put on multiple lines
    assert (
        output.text
        == r"""{% comment "Optional note" %}{{ body }}{% endcomment %}
"""
    )

    output = reformat(
        tmp_file,
        runner,
        b"""<div class="hi">
    <div class="poor">
        <p class="format">
            Lorem ipsum dolor
            <span class="bold">sit</span>
            amet
        </p>
        <img src="./pic.jpg">
    </div>
    <script src="file1.js"></script>
    {% comment %} <script src="file2.js"></script>
    <script src="file3.js"></script> {% endcomment %}
    <script src="file4.js"></script>
</div>""",
    )

    assert output.exit_code == 0

    output = reformat(
        tmp_file,
        runner,
        b"""<div class="hi">
    <div class="poor">
        {# djlint:off #}
        <p class="format">
            Lorem ipsum dolor <span class="bold">sit</span> amet
        </p>
        {# djlint:on #}
        <img src="./pic.jpg">
    </div>
    <ul>
        {% for i in items %}
            <li>item {{i}}</li>
            {% if i > 10 %}{% endif %}
            <li>item {{i}}</li>
        {% endfor %}
    </ul>
</div>
""",
    )

    assert output.exit_code == 0

    output = reformat(
        tmp_file,
        runner,
        b"""<html>
    <head>
        <script src="file1.js"></script>
        {% comment %}
        <script src="file2.js"></script>
        <script src="file3.js"></script>
        <script src="file4.js"></script>
        {% endcomment %}
        <script src="file5.js"></script>
    </head>
    <body>
    </body>
</html>
""",
    )

    assert output.exit_code == 0

    output = reformat(
        tmp_file,
        runner,
        b"""<html>
    <head>
        <script src="file1.js"></script>
        {# djlint:off #}
        {% comment %}
        <script src="file2.js"></script>
        <script src="file3.js"></script>
        <script src="file4.js"></script>
        {% endcomment %}
        {# djlint:on #}
        <script src="file5.js"></script>
    </head>
    <body>
    </body>
</html>
""",
    )

    assert output.exit_code == 0


def test_inline_comment(runner: CliRunner, tmp_file: TextIO) -> None:
    output = reformat(
        tmp_file, runner, b"{# <div></div> #}\n{% if this %}<div></div>{% endif %}"
    )
    assert output.text == """{# <div></div> #}\n{% if this %}<div></div>{% endif %}\n"""
    assert output.exit_code == 0


def test_for_loop(runner: CliRunner, tmp_file: TextIO) -> None:
    output = reformat(
        tmp_file,
        runner,
        b"""<ul>{% for athlete in athlete_list %}<li>{{ athlete.name }}</li>{% empty %}<li>Sorry, no athletes in this list.</li>{% endfor %}</ul>""",
    )
    assert output.exit_code == 1
    assert (
        output.text
        == r"""<ul>
    {% for athlete in athlete_list %}
        <li>{{ athlete.name }}</li>
    {% empty %}
        <li>Sorry, no athletes in this list.</li>
    {% endfor %}
</ul>
"""
    )


def test_filter(runner: CliRunner, tmp_file: TextIO) -> None:
    output = reformat(
        tmp_file,
        runner,
        b"""{% filter force_escape|lower %}This text will be HTML-escaped, and will appear in all lowercase.{% endfilter %}""",
    )
    assert output.exit_code == 1
    assert (
        output.text
        == r"""{% filter force_escape|lower %}
    This text will be HTML-escaped, and will appear in all lowercase.
{% endfilter %}
"""
    )


def test_if(runner: CliRunner, tmp_file: TextIO) -> None:
    output = reformat(
        tmp_file,
        runner,
        b"""{% if athlete_list %}Number of athletes: {{ athlete_list|length }}{% elif athlete_in_locker_room_list %}Athletes should be out of the locker room soon!{% else %}No athletes.{% endif %}""",
    )
    assert output.exit_code == 1
    assert (
        output.text
        == r"""{% if athlete_list %}
    Number of athletes: {{ athlete_list|length }}
{% elif athlete_in_locker_room_list %}
    Athletes should be out of the locker room soon!
{% else %}
    No athletes.
{% endif %}
"""
    )


def test_ifchanged(runner: CliRunner, tmp_file: TextIO) -> None:
    output = reformat(
        tmp_file,
        runner,
        b"""{% for match in matches %}<div style="background-color:"pink">{% ifchanged match.ballot_id %}{% cycle "red" "blue" %}{% else %}gray{% endifchanged %}{{ match }}</div>{% endfor %}""",
    )
    assert output.exit_code == 1
    assert (
        output.text
        == r"""{% for match in matches %}
    <div style="background-color:"pink">
        {% ifchanged match.ballot_id %}
            {% cycle "red" "blue" %}
        {% else %}
            gray
        {% endifchanged %}
        {{ match }}
    </div>
{% endfor %}
"""
    )


def test_include(runner: CliRunner, tmp_file: TextIO) -> None:
    output = reformat(tmp_file, runner, b"""{% include "this" %}{% include "that"%}""")
    assert output.exit_code == 1
    assert (
        output.text
        == r"""{% include "this" %}
{% include "that" %}
"""
    )


def test_spaceless(runner: CliRunner, tmp_file: TextIO) -> None:
    output = reformat(
        tmp_file,
        runner,
        b"""{% spaceless %}<p><a href="foo/">Foo</a></p>{% endspaceless %}""",
    )
    assert output.exit_code == 1
    assert (
        output.text
        == r"""{% spaceless %}
    <p>
        <a href="foo/">Foo</a>
    </p>
{% endspaceless %}
"""
    )


def test_templatetag(runner: CliRunner, tmp_file: TextIO) -> None:
    output = reformat(
        tmp_file,
        runner,
        b"""{% templatetag openblock %} url 'entry_list' {% templatetag closeblock %}""",
    )
    assert output.exit_code == 0
    assert (
        output.text
        == r"""{% templatetag openblock %} url 'entry_list' {% templatetag closeblock %}
"""
    )


def test_verbatim(runner: CliRunner, tmp_file: TextIO) -> None:
    output = reformat(
        tmp_file, runner, b"""{% verbatim %}Still alive.{% endverbatim %}"""
    )
    assert output.exit_code == 1
    assert (
        output.text
        == r"""{% verbatim %}
    Still alive.
{% endverbatim %}
"""
    )


def test_blocktranslate(runner: CliRunner, tmp_file: TextIO) -> None:
    output = reformat(
        tmp_file,
        runner,
        b"""{% blocktranslate %}The width is: {{ width }}{% endblocktranslate %}""",
    )
    assert output.exit_code == 0
    assert (
        output.text
        == r"""{% blocktranslate %}The width is: {{ width }}{% endblocktranslate %}
"""
    )

    output = reformat(
        tmp_file,
        runner,
        b"""{% blocktranslate trimmed %}The width is: {{ width }}{% endblocktranslate %}""",
    )
    assert output.exit_code == 0

    output = reformat(
        tmp_file,
        runner,
        b"""{% blocktrans %}The width is: {{ width }}{% endblocktrans %}""",
    )
    assert output.exit_code == 0
    assert (
        output.text
        == r"""{% blocktrans %}The width is: {{ width }}{% endblocktrans %}
"""
    )

    output = reformat(
        tmp_file,
        runner,
        b"""{% blocktrans trimmed %}The width is: {{ width }}{% endblocktrans %}""",
    )
    assert output.exit_code == 0

    output = reformat(
        tmp_file,
        runner,
        b"""<p>
    {% blocktrans %}If you have not created an account yet, then please
    <a href="{{ signup_url }}">sign up</a> first.{% endblocktrans %}
</p>\n""",
    )
    assert output.exit_code == 0


def test_trans(runner: CliRunner, tmp_file: TextIO) -> None:
    output = reformat(
        tmp_file, runner, b"""<p>{% trans 'Please do <b>Blah</b>.' %}</p>"""
    )
    assert output.exit_code == 1
    assert (
        """<p>
    {% trans 'Please do <b>Blah</b>.' %}
</p>
"""
        in output.text
    )


def test_with(runner: CliRunner, tmp_file: TextIO) -> None:
    output = reformat(
        tmp_file,
        runner,
        b"""{% with total=business.employees.count %}{{ total }}<div>employee</div>{{ total|pluralize }}{% endwith %}""",
    )
    assert output.exit_code == 1
    assert (
        output.text
        == r"""{% with total=business.employees.count %}
    {{ total }}
    <div>employee</div>
    {{ total|pluralize }}
{% endwith %}
"""
    )


def test_load_tag(runner: CliRunner, tmp_file: TextIO) -> None:
    output = reformat(
        tmp_file,
        runner,
        b"""{% block content %}{% load i18n %}{% endblock %}""",
    )
    assert output.exit_code == 1
    assert (
        output.text
        == r"""{% block content %}
    {% load i18n %}
{% endblock %}
"""
    )


def test_single_line_tag(runner: CliRunner, tmp_file: TextIO) -> None:
    output = reformat(
        tmp_file,
        runner,
        b"""{% if messages|length %}{% for message in messages %}{{ message }}{% endfor %}{% endif %}""",
    )
    assert output.exit_code == 1
    assert (
        output.text
        == r"""{% if messages|length %}
    {% for message in messages %}{{ message }}{% endfor %}
{% endif %}
"""
    )


def test_multiple_endblocks(runner: CliRunner, tmp_file: TextIO) -> None:
    output = reformat(
        tmp_file,
        runner,
        b"""{% block content %}{% block scripts %}{% endblock %}{% endblock %}""",
    )
    assert output.exit_code == 1
    assert (
        """{% block content %}\n    {% block scripts %}{% endblock %}\n{% endblock %}
"""
        == output.text
    )
