const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function runE2ETest() {
  const results = {
    passed: [],
    failed: [],
    screenshots: []
  };

  let browser;
  try {
    console.log('🚀 Spouštím E2E test ANT HILL aplikace...\n');

    browser = await puppeteer.launch({
      headless: false,
      defaultViewport: { width: 1920, height: 1080 }
    });

    const page = await browser.newPage();

    // Sběr console logů
    page.on('console', msg => console.log('BROWSER CONSOLE:', msg.text()));
    page.on('pageerror', err => console.log('BROWSER ERROR:', err.toString()));

    // ===== TEST 1: Backend Health Check =====
    console.log('📡 TEST 1: Backend Health Check');
    try {
      const healthResponse = await page.goto('http://localhost:8000/health', {
        waitUntil: 'networkidle0',
        timeout: 10000
      });

      const healthData = await healthResponse.json();

      if (healthData.status === 'ok') {
        results.passed.push('✅ Backend health check - status OK');
        console.log('✅ Backend health check OK:', healthData);
      } else {
        results.failed.push('❌ Backend health check - status není OK');
        console.log('❌ Backend health check FAILED:', healthData);
      }
    } catch (error) {
      results.failed.push('❌ Backend health check - endpoint nedostupný: ' + error.message);
      console.log('❌ Backend health check ERROR:', error.message);
    }

    // ===== TEST 2: Frontend Landing Page =====
    console.log('\n🏠 TEST 2: Frontend Landing Page');
    try {
      await page.goto('http://localhost:5173', {
        waitUntil: 'networkidle0',
        timeout: 10000
      });

      await sleep(3000); // Počkat na kompletní načtení

      const screenshotPath = path.join(__dirname, 'screenshots', 'landing_page.png');
      await page.screenshot({ path: screenshotPath, fullPage: true });
      results.screenshots.push(screenshotPath);
      results.passed.push('✅ Frontend landing page načten');
      console.log('✅ Frontend landing page OK, screenshot: ' + screenshotPath);
    } catch (error) {
      results.failed.push('❌ Frontend landing page - nedostupný: ' + error.message);
      console.log('❌ Frontend landing page ERROR:', error.message);
    }

    // ===== TEST 3: Marketplace Navigation =====
    console.log('\n🎯 TEST 3: Marketplace Navigation');
    try {
      // Hledat marketplace link
      const marketplaceSelectors = [
        'a[href*="marketplace"]',
        'text/Marketplace',
        'a:has-text("🎯")',
        'nav a:nth-child(2)' // Druhý link v navigaci
      ];

      let clicked = false;
      for (const selector of marketplaceSelectors) {
        try {
          await page.click(selector, { timeout: 2000 });
          clicked = true;
          break;
        } catch (e) {
          // Zkusit další selektor
        }
      }

      if (!clicked) {
        throw new Error('Marketplace link nenalezen');
      }

      await sleep(2000);

      const screenshotPath = path.join(__dirname, 'screenshots', 'marketplace.png');
      await page.screenshot({ path: screenshotPath, fullPage: true });
      results.screenshots.push(screenshotPath);

      // Zkontrolovat, že se zobrazují tasky
      const tasksVisible = await page.evaluate(() => {
        return document.body.innerText.toLowerCase().includes('task') ||
               document.querySelector('[class*="task"]') !== null ||
               document.querySelector('[class*="card"]') !== null;
      });

      if (tasksVisible) {
        results.passed.push('✅ Marketplace zobrazuje tasky');
        console.log('✅ Marketplace OK, screenshot: ' + screenshotPath);
      } else {
        results.failed.push('⚠️ Marketplace nenašel žádné tasky');
        console.log('⚠️ Marketplace bez tasków, screenshot: ' + screenshotPath);
      }
    } catch (error) {
      results.failed.push('❌ Marketplace navigation - selhala: ' + error.message);
      console.log('❌ Marketplace navigation ERROR:', error.message);
    }

    // ===== TEST 4: Notification Creation =====
    console.log('\n🔔 TEST 4: Notification Creation');
    try {
      // Otevřít nový tab pro vytvoření notifikace
      const notificationPage = await browser.newPage();
      const response = await notificationPage.goto(
        'http://localhost:8000/api/notifications/test/create-sample',
        { waitUntil: 'networkidle0', timeout: 10000 }
      );

      const notificationData = await response.json();
      console.log('📨 Notification response:', notificationData);

      if (notificationData && notificationData.id) {
        results.passed.push('✅ Notification vytvořena s ID: ' + notificationData.id);

        // Zavřít notification tab a vrátit se na frontend
        await notificationPage.close();

        // Počkat 15 sekund na polling
        console.log('⏳ Čekám 15 sekund na polling notifikace...');
        await sleep(15000);

        const screenshotPath = path.join(__dirname, 'screenshots', 'notification.png');
        await page.screenshot({ path: screenshotPath, fullPage: true });
        results.screenshots.push(screenshotPath);

        // Zkontrolovat, zda se objevil toast
        const toastVisible = await page.evaluate(() => {
          const toast = document.querySelector('[class*="toast"], [class*="notification"], [role="alert"]');
          return toast !== null;
        });

        if (toastVisible) {
          results.passed.push('✅ Toast notification se zobrazil');
          console.log('✅ Toast notification OK, screenshot: ' + screenshotPath);
        } else {
          results.failed.push('⚠️ Toast notification se nezobrazil (možná už zmizel)');
          console.log('⚠️ Toast notification nebyl nalezen, screenshot: ' + screenshotPath);
        }
      } else {
        throw new Error('Notification response neobsahuje ID');
      }
    } catch (error) {
      results.failed.push('❌ Notification creation - selhala: ' + error.message);
      console.log('❌ Notification creation ERROR:', error.message);
    }

    // ===== TEST 5: Leaderboard =====
    console.log('\n🏆 TEST 5: Leaderboard');
    try {
      // Hledat leaderboard link
      const leaderboardSelectors = [
        'a[href*="leaderboard"]',
        'text/Leaderboard',
        'a:has-text("🏆")',
        'nav a:nth-child(3)' // Třetí link v navigaci
      ];

      let clicked = false;
      for (const selector of leaderboardSelectors) {
        try {
          await page.click(selector, { timeout: 2000 });
          clicked = true;
          break;
        } catch (e) {
          // Zkusit další selektor
        }
      }

      if (!clicked) {
        throw new Error('Leaderboard link nenalezen');
      }

      await sleep(2000);

      const screenshotPath = path.join(__dirname, 'screenshots', 'leaderboard.png');
      await page.screenshot({ path: screenshotPath, fullPage: true });
      results.screenshots.push(screenshotPath);

      // Zkontrolovat, že se zobrazuje tabulka
      const tableVisible = await page.evaluate(() => {
        return document.querySelector('table') !== null ||
               document.querySelector('[class*="table"]') !== null ||
               document.querySelector('[class*="leaderboard"]') !== null;
      });

      if (tableVisible) {
        results.passed.push('✅ Leaderboard zobrazuje tabulku');
        console.log('✅ Leaderboard OK, screenshot: ' + screenshotPath);
      } else {
        results.failed.push('⚠️ Leaderboard tabulka nenalezena');
        console.log('⚠️ Leaderboard bez tabulky, screenshot: ' + screenshotPath);
      }
    } catch (error) {
      results.failed.push('❌ Leaderboard - selhalo: ' + error.message);
      console.log('❌ Leaderboard ERROR:', error.message);
    }

  } catch (error) {
    console.error('💥 Kritická chyba:', error);
    results.failed.push('💥 Kritická chyba: ' + error.message);
  } finally {
    if (browser) {
      await browser.close();
    }
  }

  // ===== FINAL REPORT =====
  console.log('\n' + '='.repeat(60));
  console.log('📊 E2E TEST REPORT - ANT HILL');
  console.log('='.repeat(60));

  console.log('\n✅ CO FUNGUJE:');
  results.passed.forEach(item => console.log('  ' + item));

  console.log('\n❌ CO NEFUNGUJE:');
  if (results.failed.length === 0) {
    console.log('  Vše funguje perfektně! 🎉');
  } else {
    results.failed.forEach(item => console.log('  ' + item));
  }

  console.log('\n📸 SCREENSHOTS:');
  results.screenshots.forEach(path => console.log('  ' + path));

  console.log('\n' + '='.repeat(60));

  // Uložit report do souboru
  const reportPath = path.join(__dirname, 'e2e_test_report.txt');
  const reportContent = `
E2E TEST REPORT - ANT HILL
Generated: ${new Date().toISOString()}

✅ CO FUNGUJE:
${results.passed.map(item => '  ' + item).join('\n')}

❌ CO NEFUNGUJE:
${results.failed.length === 0 ? '  Vše funguje perfektně! 🎉' : results.failed.map(item => '  ' + item).join('\n')}

📸 SCREENSHOTS:
${results.screenshots.map(path => '  ' + path).join('\n')}
`;

  fs.writeFileSync(reportPath, reportContent);
  console.log('\n📄 Report uložen do:', reportPath);
}

// Vytvoř screenshots složku
const screenshotsDir = path.join(__dirname, 'screenshots');
if (!fs.existsSync(screenshotsDir)) {
  fs.mkdirSync(screenshotsDir, { recursive: true });
}

runE2ETest().catch(console.error);
