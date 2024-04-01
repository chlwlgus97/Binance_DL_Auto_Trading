<?php
// AJAX 액션에 대한 핸들러 함수 등록
add_action('wp_ajax_get_filtered_data', 'handle_get_filtered_data');
add_action('wp_ajax_nopriv_get_filtered_data', 'handle_get_filtered_data');

function handle_get_filtered_data() {
    global $wpdb;
    // 데이터베이스 정보 설정
    $host = '?';
    $user = '?';
    $password = '?';
    $dbname = '?';
    $charset = 'utf8mb4';

    $dsn = "mysql:host={$host};dbname={$dbname};charset={$charset}";
    $options = [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        PDO::ATTR_EMULATE_PREPARES => false,
    ];

    try {
        $pdo = new PDO($dsn, $user, $password, $options);
        
        // assets 데이터 조회 - 최근 업데이트된 데이터만
        $stmt = $pdo->query("SELECT * FROM filtered_assets WHERE walletBalance > 0 ORDER BY updated_at DESC LIMIT 3");
        $assets = $stmt->fetchAll();
        
        // positions 데이터 조회 - 최근 업데이트된 데이터만
        $stmt = $pdo->query("SELECT * FROM filtered_positions WHERE entryPrice > 0 ORDER BY updated_at DESC LIMIT 3");
        $positions = $stmt->fetchAll();

        // daily_pnl 데이터 조회 - 최근 업데이트된 데이터만
        $stmt = $pdo->query("SELECT total_pnl FROM daily_pnl ORDER BY updated_at DESC LIMIT 1");
        $daily_pnl = $stmt->fetchAll(); // 결과는 배열 안에 최신 레코드만 포함될 것임

        // position_table 데이터 조회 - datatime 기준으로 최근 데이터만
        $stmt = $pdo->query("SELECT symbol, price_before_last, last_price, realizedPnl FROM position_table ORDER BY datetime DESC LIMIT 3");
        $positions_table = $stmt->fetchAll();

        // 결과를 JSON 형식으로 클라이언트에 전송
        wp_send_json_success(['assets' => $assets, 'positions' => $positions, 'daily_pnl' => $daily_pnl, 'positions_table' => $positions_table]);
    } catch (Exception $e) {
        // 오류 처리
        wp_send_json_error($e->getMessage());
    }

    wp_die(); // AJAX 요청 종료
}

// 스크립트 등록 및 로컬라이즈
function enqueue_assets_positions_script() {
    wp_enqueue_script('ajax-assets-positions', get_template_directory_uri() . '/js/ajax-assets-positions.js', ['jquery'], null, true);
    wp_localize_script('ajax-assets-positions', 'ajaxObj', ['ajaxUrl' => admin_url('admin-ajax.php')]);
}
add_action('wp_enqueue_scripts', 'enqueue_assets_positions_script');
