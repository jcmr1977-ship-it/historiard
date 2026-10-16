import streamlit.components.v1 as components

GOOGLE_ANALYTICS_ID = "G-YCZN022HR5"

components.html(
    f"""
    <script>
    (function() {{
        var d = window.parent.document;
        if (d.getElementById('ga-gtag')) return;

        var s1 = d.createElement('script');
        s1.id = 'ga-gtag';
        s1.async = true;
        s1.src = 'https://www.googletagmanager.com/gtag/js?id={GOOGLE_ANALYTICS_ID}';
        d.head.appendChild(s1);

        var s2 = d.createElement('script');
        s2.innerHTML = "window.dataLayer=window.dataLayer||[];"
                     + "function gtag(){{dataLayer.push(arguments);}}"
                     + "gtag('js', new Date());"
                     + "gtag('config', '{GOOGLE_ANALYTICS_ID}');";
        d.head.appendChild(s2);
    }})();
    </script>
    """,
    height=0, width=0,
)
