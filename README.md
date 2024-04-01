# Binance_DL_Auto_Trading Project
### - 딥러닝 모델 + 자동매매

## 🔎 프로젝트 개요
#### - Binance의 암호화폐 주가 차트 데이터를 활용하여 비트코인, 이더리움, 리플의 주가를 예측해서 자동 매매 프로그램 구축

## ⏰ 개발 기간
#### - 2023.12. ~ 2024.03.

## 👩‍👩‍👧‍👦 팀원 소개 및 역할
- 김현준(팀장) : 데이터 수집 및 모델링, 실시간 매매 구현
- 백승호 : 데이터 분석 및 모델링
- 최지현 : 웹 구현 및 모델링
- 황진영 : 데이터 수집 및 모델

## 🔧 개발 환경
- Language : Python, PHP, MySQL, JavaScript
- DB : MariaDB
- IDE : VSCode, DBeaver, MobaXterm
- Server : GoogleCloud, Apache2
- Data Sources : Binance, Investing.com, U.Today

## 🗓️ 개발 일정
![image](https://github.com/chlwlgus97/Binance_DL_Auto_Trading/assets/130372088/dcceea6a-bafa-4443-a825-a529b0a0e809)

## 📍 핵심 기능
#### 회귀 모델 + 분류 모델 동시 사용
- 분류 모델을 사용하여 주가가 상승할지 하락할지에 대한 확실성을 높이고 회귀 모델을 통해 실제로 예상되는 수익률을 계산함으로써 수수로가 발생하더라도 이익을 볼 수 있는 거래 지점을 예측

#### 1분단위 주가 예측
- 주기적으로 Binance 서버 타임을 가져와 정확히 매분 00초에 예측하게끔 수행 -> 매매 방식으로 진행

#### Binance 지갑 정보
- api_key 와 api_secret key 정보를 입력한 후 코드 이용가능 아래와 같은 정보 확인
![image](https://github.com/chlwlgus97/Binance_DL_Auto_Trading/assets/130372088/924931e6-cf72-48c7-813c-954e0b13230d)

#### Web 화면에서 현재 자산 정보 확인 가능(GCP 사용 현재 상태 : OFF)
- wordpress를 활용하여 web으로 데이터 시각화
- 사이트 주소 : http://35.216.66.247/wordpress/
![image](https://github.com/chlwlgus97/Binance_DL_Auto_Trading/assets/130372088/d641eeef-b0fc-4fdc-907f-b9a2161a0a65)

