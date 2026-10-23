package com.example.careerreadiness

import android.annotation.SuppressLint
import android.app.Activity
import android.os.Bundle
import android.view.View
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Button

/**
 * Thin WebView shell around the deployed Flask app.
 * Offline/error main-frame loads show a retry screen instead of a blank page.
 */
class MainActivity : Activity() {

    private lateinit var webView: WebView
    private lateinit var errorPanel: View
    private var lastUrl: String = BuildConfig.APP_URL

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        webView = findViewById(R.id.webView)
        errorPanel = findViewById(R.id.errorPanel)
        val retry = findViewById<Button>(R.id.retryButton)

        webView.settings.apply {
            javaScriptEnabled = true // Chart.js needs JS
            domStorageEnabled = true
        }

        webView.webViewClient = object : WebViewClient() {
            override fun onPageFinished(view: WebView, url: String) {
                lastUrl = url
                showWeb()
            }

            override fun onReceivedError(
                view: WebView,
                request: WebResourceRequest,
                error: WebResourceError
            ) {
                if (request.isForMainFrame) showError()
            }
        }

        retry.setOnClickListener {
            showWeb()
            webView.loadUrl(lastUrl)
        }

        if (savedInstanceState != null) {
            webView.restoreState(savedInstanceState)
        } else {
            webView.loadUrl(BuildConfig.APP_URL)
        }
    }

    private fun showWeb() {
        errorPanel.visibility = View.GONE
        webView.visibility = View.VISIBLE
    }

    private fun showError() {
        webView.visibility = View.GONE
        errorPanel.visibility = View.VISIBLE
    }

    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        webView.saveState(outState)
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (webView.canGoBack()) webView.goBack() else super.onBackPressed()
    }
}