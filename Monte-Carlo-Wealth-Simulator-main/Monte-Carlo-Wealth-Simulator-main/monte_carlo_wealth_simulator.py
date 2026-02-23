import streamlit as st
import numpy as np
import plotly.graph_objs as go

# --- App Config ---
st.set_page_config(
    page_title="Monte Carlo Wealth Simulator",
    layout="centered",
    initial_sidebar_state="expanded",
    page_icon="💰"
)

# --- Dark Theme Styling ---
st.markdown(
    """
    <style>
    body, .stApp { background-color: #18191A; color: #F5F6FA; }
    .st-bb { background-color: #23272F !important; }
    .st-cq { color: #FFD600 !important; }
    .st-cp { color: #FFD600 !important; }
    .st-cv { color: #FFD600 !important; }
    .st-cw { color: #FFD600 !important; }
    .st-cx { color: #FFD600 !important; }
    .st-cy { color: #FFD600 !important; }
    .st-cz { color: #FFD600 !important; }
    .st-da { color: #FFD600 !important; }
    .st-db { color: #FFD600 !important; }
    .st-dc { color: #FFD600 !important; }
    .st-dd { color: #FFD600 !important; }
    .st-de { color: #FFD600 !important; }
    .st-df { color: #FFD600 !important; }
    .st-dg { color: #FFD600 !important; }
    .st-dh { color: #FFD600 !important; }
    .st-di { color: #FFD600 !important; }
    .st-dj { color: #FFD600 !important; }
    .st-dk { color: #FFD600 !important; }
    .st-dl { color: #FFD600 !important; }
    .st-dm { color: #FFD600 !important; }
    .st-dn { color: #FFD600 !important; }
    .st-do { color: #FFD600 !important; }
    .st-dp { color: #FFD600 !important; }
    .st-dq { color: #FFD600 !important; }
    .st-dr { color: #FFD600 !important; }
    .st-ds { color: #FFD600 !important; }
    .st-dt { color: #FFD600 !important; }
    .st-du { color: #FFD600 !important; }
    .st-dv { color: #FFD600 !important; }
    .st-dw { color: #FFD600 !important; }
    .st-dx { color: #FFD600 !important; }
    .st-dy { color: #FFD600 !important; }
    .st-dz { color: #FFD600 !important; }
    .st-e0 { color: #FFD600 !important; }
    .st-e1 { color: #FFD600 !important; }
    .st-e2 { color: #FFD600 !important; }
    .st-e3 { color: #FFD600 !important; }
    .st-e4 { color: #FFD600 !important; }
    .st-e5 { color: #FFD600 !important; }
    .st-e6 { color: #FFD600 !important; }
    .st-e7 { color: #FFD600 !important; }
    .st-e8 { color: #FFD600 !important; }
    .st-e9 { color: #FFD600 !important; }
    .st-ea { color: #FFD600 !important; }
    .st-eb { color: #FFD600 !important; }
    .st-ec { color: #FFD600 !important; }
    .st-ed { color: #FFD600 !important; }
    .st-ee { color: #FFD600 !important; }
    .st-ef { color: #FFD600 !important; }
    .st-eg { color: #FFD600 !important; }
    .st-eh { color: #FFD600 !important; }
    .st-ei { color: #FFD600 !important; }
    .st-ej { color: #FFD600 !important; }
    .st-ek { color: #FFD600 !important; }
    .st-el { color: #FFD600 !important; }
    .st-em { color: #FFD600 !important; }
    .st-en { color: #FFD600 !important; }
    .st-eo { color: #FFD600 !important; }
    .st-ep { color: #FFD600 !important; }
    .st-eq { color: #FFD600 !important; }
    .st-er { color: #FFD600 !important; }
    .st-es { color: #FFD600 !important; }
    .st-et { color: #FFD600 !important; }
    .st-eu { color: #FFD600 !important; }
    .st-ev { color: #FFD600 !important; }
    .st-ew { color: #FFD600 !important; }
    .st-ex { color: #FFD600 !important; }
    .st-ey { color: #FFD600 !important; }
    .st-ez { color: #FFD600 !important; }
    .st-f0 { color: #FFD600 !important; }
    .st-f1 { color: #FFD600 !important; }
    .st-f2 { color: #FFD600 !important; }
    .st-f3 { color: #FFD600 !important; }
    .st-f4 { color: #FFD600 !important; }
    .st-f5 { color: #FFD600 !important; }
    .st-f6 { color: #FFD600 !important; }
    .st-f7 { color: #FFD600 !important; }
    .st-f8 { color: #FFD600 !important; }
    .st-f9 { color: #FFD600 !important; }
    .st-fa { color: #FFD600 !important; }
    .st-fb { color: #FFD600 !important; }
    .st-fc { color: #FFD600 !important; }
    .st-fd { color: #FFD600 !important; }
    .st-fe { color: #FFD600 !important; }
    .st-ff { color: #FFD600 !important; }
    .st-fg { color: #FFD600 !important; }
    .st-fh { color: #FFD600 !important; }
    .st-fi { color: #FFD600 !important; }
    .st-fj { color: #FFD600 !important; }
    .st-fk { color: #FFD600 !important; }
    .st-fl { color: #FFD600 !important; }
    .st-fm { color: #FFD600 !important; }
    .st-fn { color: #FFD600 !important; }
    .st-fo { color: #FFD600 !important; }
    .st-fp { color: #FFD600 !important; }
    .st-fq { color: #FFD600 !important; }
    .st-fr { color: #FFD600 !important; }
    .st-fs { color: #FFD600 !important; }
    .st-ft { color: #FFD600 !important; }
    .st-fu { color: #FFD600 !important; }
    .st-fv { color: #FFD600 !important; }
    .st-fw { color: #FFD600 !important; }
    .st-fx { color: #FFD600 !important; }
    .st-fy { color: #FFD600 !important; }
    .st-fz { color: #FFD600 !important; }
    .st-g0 { color: #FFD600 !important; }
    .st-g1 { color: #FFD600 !important; }
    .st-g2 { color: #FFD600 !important; }
    .st-g3 { color: #FFD600 !important; }
    .st-g4 { color: #FFD600 !important; }
    .st-g5 { color: #FFD600 !important; }
    .st-g6 { color: #FFD600 !important; }
    .st-g7 { color: #FFD600 !important; }
    .st-g8 { color: #FFD600 !important; }
    .st-g9 { color: #FFD600 !important; }
    .st-ga { color: #FFD600 !important; }
    .st-gb { color: #FFD600 !important; }
    .st-gc { color: #FFD600 !important; }
    .st-gd { color: #FFD600 !important; }
    .st-ge { color: #FFD600 !important; }
    .st-gf { color: #FFD600 !important; }
    .st-gg { color: #FFD600 !important; }
    .st-gh { color: #FFD600 !important; }
    .st-gi { color: #FFD600 !important; }
    .st-gj { color: #FFD600 !important; }
    .st-gk { color: #FFD600 !important; }
    .st-gl { color: #FFD600 !important; }
    .st-gm { color: #FFD600 !important; }
    .st-gn { color: #FFD600 !important; }
    .st-go { color: #FFD600 !important; }
    .st-gp { color: #FFD600 !important; }
    .st-gq { color: #FFD600 !important; }
    .st-gr { color: #FFD600 !important; }
    .st-gs { color: #FFD600 !important; }
    .st-gt { color: #FFD600 !important; }
    .st-gu { color: #FFD600 !important; }
    .st-gv { color: #FFD600 !important; }
    .st-gw { color: #FFD600 !important; }
    .st-gx { color: #FFD600 !important; }
    .st-gy { color: #FFD600 !important; }
    .st-gz { color: #FFD600 !important; }
    .st-ha { color: #FFD600 !important; }
    .st-hb { color: #FFD600 !important; }
    .st-hc { color: #FFD600 !important; }
    .st-hd { color: #FFD600 !important; }
    .st-he { color: #FFD600 !important; }
    .st-hf { color: #FFD600 !important; }
    .st-hg { color: #FFD600 !important; }
    .st-hh { color: #FFD600 !important; }
    .st-hi { color: #FFD600 !important; }
    .st-hj { color: #FFD600 !important; }
    .st-hk { color: #FFD600 !important; }
    .st-hl { color: #FFD600 !important; }
    .st-hm { color: #FFD600 !important; }
    .st-hn { color: #FFD600 !important; }
    .st-ho { color: #FFD600 !important; }
    .st-hp { color: #FFD600 !important; }
    .st-hq { color: #FFD600 !important; }
    .st-hr { color: #FFD600 !important; }
    .st-hs { color: #FFD600 !important; }
    .st-ht { color: #FFD600 !important; }
    .st-hu { color: #FFD600 !important; }
    .st-hv { color: #FFD600 !important; }
    .st-hw { color: #FFD600 !important; }
    .st-hx { color: #FFD600 !important; }
    .st-hy { color: #FFD600 !important; }
    .st-hz { color: #FFD600 !important; }
    .st-i0 { color: #FFD600 !important; }
    .st-i1 { color: #FFD600 !important; }
    .st-i2 { color: #FFD600 !important; }
    .st-i3 { color: #FFD600 !important; }
    .st-i4 { color: #FFD600 !important; }
    .st-i5 { color: #FFD600 !important; }
    .st-i6 { color: #FFD600 !important; }
    .st-i7 { color: #FFD600 !important; }
    .st-i8 { color: #FFD600 !important; }
    .st-i9 { color: #FFD600 !important; }
    .st-ia { color: #FFD600 !important; }
    .st-ib { color: #FFD600 !important; }
    .st-ic { color: #FFD600 !important; }
    .st-id { color: #FFD600 !important; }
    .st-ie { color: #FFD600 !important; }
    .st-if { color: #FFD600 !important; }
    .st-ig { color: #FFD600 !important; }
    .st-ih { color: #FFD600 !important; }
    .st-ii { color: #FFD600 !important; }
    .st-ij { color: #FFD600 !important; }
    .st-ik { color: #FFD600 !important; }
    .st-il { color: #FFD600 !important; }
    .st-im { color: #FFD600 !important; }
    .st-in { color: #FFD600 !important; }
    .st-io { color: #FFD600 !important; }
    .st-ip { color: #FFD600 !important; }
    .st-iq { color: #FFD600 !important; }
    .st-ir { color: #FFD600 !important; }
    .st-is { color: #FFD600 !important; }
    .st-it { color: #FFD600 !important; }
    .st-iu { color: #FFD600 !important; }
    .st-iv { color: #FFD600 !important; }
    .st-iw { color: #FFD600 !important; }
    .st-ix { color: #FFD600 !important; }
    .st-iy { color: #FFD600 !important; }
    .st-iz { color: #FFD600 !important; }
    .st-j0 { color: #FFD600 !important; }
    .st-j1 { color: #FFD600 !important; }
    .st-j2 { color: #FFD600 !important; }
    .st-j3 { color: #FFD600 !important; }
    .st-j4 { color: #FFD600 !important; }
    .st-j5 { color: #FFD600 !important; }
    .st-j6 { color: #FFD600 !important; }
    .st-j7 { color: #FFD600 !important; }
    .st-j8 { color: #FFD600 !important; }
    .st-j9 { color: #FFD600 !important; }
    .st-ja { color: #FFD600 !important; }
    .st-jb { color: #FFD600 !important; }
    .st-jc { color: #FFD600 !important; }
    .st-jd { color: #FFD600 !important; }
    .st-je { color: #FFD600 !important; }
    .st-jf { color: #FFD600 !important; }
    .st-jg { color: #FFD600 !important; }
    .st-jh { color: #FFD600 !important; }
    .st-ji { color: #FFD600 !important; }
    .st-jj { color: #FFD600 !important; }
    .st-jk { color: #FFD600 !important; }
    .st-jl { color: #FFD600 !important; }
    .st-jm { color: #FFD600 !important; }
    .st-jn { color: #FFD600 !important; }
    .st-jo { color: #FFD600 !important; }
    .st-jp { color: #FFD600 !important; }
    .st-jq { color: #FFD600 !important; }
    .st-jr { color: #FFD600 !important; }
    .st-js { color: #FFD600 !important; }
    .st-jt { color: #FFD600 !important; }
    .st-ju { color: #FFD600 !important; }
    .st-jv { color: #FFD600 !important; }
    .st-jw { color: #FFD600 !important; }
    .st-jx { color: #FFD600 !important; }
    .st-jy { color: #FFD600 !important; }
    .st-jz { color: #FFD600 !important; }
    .st-k0 { color: #FFD600 !important; }
    .st-k1 { color: #FFD600 !important; }
    .st-k2 { color: #FFD600 !important; }
    .st-k3 { color: #FFD600 !important; }
    .st-k4 { color: #FFD600 !important; }
    .st-k5 { color: #FFD600 !important; }
    .st-k6 { color: #FFD600 !important; }
    .st-k7 { color: #FFD600 !important; }
    .st-k8 { color: #FFD600 !important; }
    .st-k9 { color: #FFD600 !important; }
    .st-ka { color: #FFD600 !important; }
    .st-kb { color: #FFD600 !important; }
    .st-kc { color: #FFD600 !important; }
    .st-kd { color: #FFD600 !important; }
    .st-ke { color: #FFD600 !important; }
    .st-kf { color: #FFD600 !important; }
    .st-kg { color: #FFD600 !important; }
    .st-kh { color: #FFD600 !important; }
    .st-ki { color: #FFD600 !important; }
    .st-kj { color: #FFD600 !important; }
    .st-kk { color: #FFD600 !important; }
    .st-kl { color: #FFD600 !important; }
    .st-km { color: #FFD600 !important; }
    .st-kn { color: #FFD600 !important; }
    .st-ko { color: #FFD600 !important; }
    .st-kp { color: #FFD600 !important; }
    .st-kq { color: #FFD600 !important; }
    .st-kr { color: #FFD600 !important; }
    .st-ks { color: #FFD600 !important; }
    .st-kt { color: #FFD600 !important; }
    .st-ku { color: #FFD600 !important; }
    .st-kv { color: #FFD600 !important; }
    .st-kw { color: #FFD600 !important; }
    .st-kx { color: #FFD600 !important; }
    .st-ky { color: #FFD600 !important; }
    .st-kz { color: #FFD600 !important; }
    .st-l0 { color: #FFD600 !important; }
    .st-l1 { color: #FFD600 !important; }
    .st-l2 { color: #FFD600 !important; }
    .st-l3 { color: #FFD600 !important; }
    .st-l4 { color: #FFD600 !important; }
    .st-l5 { color: #FFD600 !important; }
    .st-l6 { color: #FFD600 !important; }
    .st-l7 { color: #FFD600 !important; }
    .st-l8 { color: #FFD600 !important; }
    .st-l9 { color: #FFD600 !important; }
    .st-la { color: #FFD600 !important; }
    .st-lb { color: #FFD600 !important; }
    .st-lc { color: #FFD600 !important; }
    .st-ld { color: #FFD600 !important; }
    .st-le { color: #FFD600 !important; }
    .st-lf { color: #FFD600 !important; }
    .st-lg { color: #FFD600 !important; }
    .st-lh { color: #FFD600 !important; }
    .st-li { color: #FFD600 !important; }
    .st-lj { color: #FFD600 !important; }
    .st-lk { color: #FFD600 !important; }
    .st-ll { color: #FFD600 !important; }
    .st-lm { color: #FFD600 !important; }
    .st-ln { color: #FFD600 !important; }
    .st-lo { color: #FFD600 !important; }
    .st-lp { color: #FFD600 !important; }
    .st-lq { color: #FFD600 !important; }
    .st-lr { color: #FFD600 !important; }
    .st-ls { color: #FFD600 !important; }
    .st-lt { color: #FFD600 !important; }
    .st-lu { color: #FFD600 !important; }
    .st-lv { color: #FFD600 !important; }
    .st-lw { color: #FFD600 !important; }
    .st-lx { color: #FFD600 !important; }
    .st-ly { color: #FFD600 !important; }
    .st-lz { color: #FFD600 !important; }
    .st-m0 { color: #FFD600 !important; }
    .st-m1 { color: #FFD600 !important; }
    .st-m2 { color: #FFD600 !important; }
    .st-m3 { color: #FFD600 !important; }
    .st-m4 { color: #FFD600 !important; }
    .st-m5 { color: #FFD600 !important; }
    .st-m6 { color: #FFD600 !important; }
    .st-m7 { color: #FFD600 !important; }
    .st-m8 { color: #FFD600 !important; }
    .st-m9 { color: #FFD600 !important; }
    .st-ma { color: #FFD600 !important; }
    .st-mb { color: #FFD600 !important; }
    .st-mc { color: #FFD600 !important; }
    .st-md { color: #FFD600 !important; }
    .st-me { color: #FFD600 !important; }
    .st-mf { color: #FFD600 !important; }
    .st-mg { color: #FFD600 !important; }
    .st-mh { color: #FFD600 !important; }
    .st-mi { color: #FFD600 !important; }
    .st-mj { color: #FFD600 !important; }
    .st-mk { color: #FFD600 !important; }
    .st-ml { color: #FFD600 !important; }
    .st-mm { color: #FFD600 !important; }
    .st-mn { color: #FFD600 !important; }
    .st-mo { color: #FFD600 !important; }
    .st-mp { color: #FFD600 !important; }
    .st-mq { color: #FFD600 !important; }
    .st-mr { color: #FFD600 !important; }
    .st-ms { color: #FFD600 !important; }
    .st-mt { color: #FFD600 !important; }
    .st-mu { color: #FFD600 !important; }
    .st-mv { color: #FFD600 !important; }
    .st-mw { color: #FFD600 !important; }
    .st-mx { color: #FFD600 !important; }
    .st-my { color: #FFD600 !important; }
    .st-mz { color: #FFD600 !important; }
    .st-n0 { color: #FFD600 !important; }
    .st-n1 { color: #FFD600 !important; }
    .st-n2 { color: #FFD600 !important; }
    .st-n3 { color: #FFD600 !important; }
    .st-n4 { color: #FFD600 !important; }
    .st-n5 { color: #FFD600 !important; }
    .st-n6 { color: #FFD600 !important; }
    .st-n7 { color: #FFD600 !important; }
    .st-n8 { color: #FFD600 !important; }
    .st-n9 { color: #FFD600 !important; }
    .st-na { color: #FFD600 !important; }
    .st-nb { color: #FFD600 !important; }
    .st-nc { color: #FFD600 !important; }
    .st-nd { color: #FFD600 !important; }
    .st-ne { color: #FFD600 !important; }
    .st-nf { color: #FFD600 !important; }
    .st-ng { color: #FFD600 !important; }
    .st-nh { color: #FFD600 !important; }
    .st-ni { color: #FFD600 !important; }
    .st-nj { color: #FFD600 !important; }
    .st-nk { color: #FFD600 !important; }
    .st-nl { color: #FFD600 !important; }
    .st-nm { color: #FFD600 !important; }
    .st-nn { color: #FFD600 !important; }
    .st-no { color: #FFD600 !important; }
    .st-np { color: #FFD600 !important; }
    .st-nq { color: #FFD600 !important; }
    .st-nr { color: #FFD600 !important; }
    .st-ns { color: #FFD600 !important; }
    .st-nt { color: #FFD600 !important; }
    .st-nu { color: #FFD600 !important; }
    .st-nv { color: #FFD600 !important; }
    .st-nw { color: #FFD600 !important; }
    .st-nx { color: #FFD600 !important; }
    .st-ny { color: #FFD600 !important; }
    .st-nz { color: #FFD600 !important; }
    .st-o0 { color: #FFD600 !important; }
    .st-o1 { color: #FFD600 !important; }
    .st-o2 { color: #FFD600 !important; }
    .st-o3 { color: #FFD600 !important; }
    .st-o4 { color: #FFD600 !important; }
    .st-o5 { color: #FFD600 !important; }
    .st-o6 { color: #FFD600 !important; }
    .st-o7 { color: #FFD600 !important; }
    .st-o8 { color: #FFD600 !important; }
    .st-o9 { color: #FFD600 !important; }
    .st-oa { color: #FFD600 !important; }
    .st-ob { color: #FFD600 !important; }
    .st-oc { color: #FFD600 !important; }
    .st-od { color: #FFD600 !important; }
    .st-oe { color: #FFD600 !important; }
    .st-of { color: #FFD600 !important; }
    .st-og { color: #FFD600 !important; }
    .st-oh { color: #FFD600 !important; }
    .st-oi { color: #FFD600 !important; }
    .st-oj { color: #FFD600 !important; }
    .st-ok { color: #FFD600 !important; }
    .st-ol { color: #FFD600 !important; }
    .st-om { color: #FFD600 !important; }
    .st-on { color: #FFD600 !important; }
    .st-oo { color: #FFD600 !important; }
    .st-op { color: #FFD600 !important; }
    .st-oq { color: #FFD600 !important; }
    .st-or { color: #FFD600 !important; }
    .st-os { color: #FFD600 !important; }
    .st-ot { color: #FFD600 !important; }
    .st-ou { color: #FFD600 !important; }
    .st-ov { color: #FFD600 !important; }
    .st-ow { color: #FFD600 !important; }
    .st-ox { color: #FFD600 !important; }
    .st-oy { color: #FFD600 !important; }
    .st-oz { color: #FFD600 !important; }
    .st-p0 { color: #FFD600 !important; }
    .st-p1 { color: #FFD600 !important; }
    .st-p2 { color: #FFD600 !important; }
    .st-p3 { color: #FFD600 !important; }
    .st-p4 { color: #FFD600 !important; }
    .st-p5 { color: #FFD600 !important; }
    .st-p6 { color: #FFD600 !important; }
    .st-p7 { color: #FFD600 !important; }
    .st-p8 { color: #FFD600 !important; }
    .st-p9 { color: #FFD600 !important; }
    .st-pa { color: #FFD600 !important; }
    .st-pb { color: #FFD600 !important; }
    .st-pc { color: #FFD600 !important; }
    .st-pd { color: #FFD600 !important; }
    .st-pe { color: #FFD600 !important; }
    .st-pf { color: #FFD600 !important; }
    .st-pg { color: #FFD600 !important; }
    .st-ph { color: #FFD600 !important; }
    .st-pi { color: #FFD600 !important; }
    .st-pj { color: #FFD600 !important; }
    .st-pk { color: #FFD600 !important; }
    .st-pl { color: #FFD600 !important; }
    .st-pm { color: #FFD600 !important; }
    .st-pn { color: #FFD600 !important; }
    .st-po { color: #FFD600 !important; }
    .st-pp { color: #FFD600 !important; }
    .st-pq { color: #FFD600 !important; }
    .st-pr { color: #FFD600 !important; }
    .st-ps { color: #FFD600 !important; }
    .st-pt { color: #FFD600 !important; }
    .st-pu { color: #FFD600 !important; }
    .st-pv { color: #FFD600 !important; }
    .st-pw { color: #FFD600 !important; }
    .st-px { color: #FFD600 !important; }
    .st-py { color: #FFD600 !important; }
    .st-pz { color: #FFD600 !important; }
    .st-q0 { color: #FFD600 !important; }
    .st-q1 { color: #FFD600 !important; }
    .st-q2 { color: #FFD600 !important; }
    .st-q3 { color: #FFD600 !important; }
    .st-q4 { color: #FFD600 !important; }
    .st-q5 { color: #FFD600 !important; }
    .st-q6 { color: #FFD600 !important; }
    .st-q7 { color: #FFD600 !important; }
    .st-q8 { color: #FFD600 !important; }
    .st-q9 { color: #FFD600 !important; }
    .st-qa { color: #FFD600 !important; }
    .st-qb { color: #FFD600 !important; }
    .st-qc { color: #FFD600 !important; }
    .st-qd { color: #FFD600 !important; }
    .st-qe { color: #FFD600 !important; }
    .st-qf { color: #FFD600 !important; }
    .st-qg { color: #FFD600 !important; }
    .st-qh { color: #FFD600 !important; }
    .st-qi { color: #FFD600 !important; }
    .st-qj { color: #FFD600 !important; }
    .st-qk { color: #FFD600 !important; }
    .st-ql { color: #FFD600 !important; }
    .st-qm { color: #FFD600 !important; }
    .st-qn { color: #FFD600 !important; }
    .st-qp { color: #FFD600 !important; }
    .st-qq { color: #FFD600 !important; }
    .st-qr { color: #FFD600 !important; }
    .st-qs { color: #FFD600 !important; }
    .st-qt { color: #FFD600 !important; }
    .st-qu { color: #FFD600 !important; }
    .st-qv { color: #FFD600 !important; }
    .st-qw { color: #FFD600 !important; }
    .st-qx { color: #FFD600 !important; }
    .st-qy { color: #FFD600 !important; }
    .st-qz { color: #FFD600 !important; }
    .st-r0 { color: #FFD600 !important; }
    .st-r1 { color: #FFD600 !important; }
    .st-r2 { color: #FFD600 !important; }
    .st-r3 { color: #FFD600 !important; }
    .st-r4 { color: #FFD600 !important; }
    .st-r5 { color: #FFD600 !important; }
    .st-r6 { color: #FFD600 !important; }
    .st-r7 { color: #FFD600 !important; }
    .st-r8 { color: #FFD600 !important; }
    .st-r9 { color: #FFD600 !important; }
    .st-ra { color: #FFD600 !important; }
    .st-rb { color: #FFD600 !important; }
    .st-rc { color: #FFD600 !important; }
    .st-rd { color: #FFD600 !important; }
    .st-re { color: #FFD600 !important; }
    .st-rf { color: #FFD600 !important; }
    .st-rg { color: #FFD600 !important; }
    .st-rh { color: #FFD600 !important; }
    .st-ri { color: #FFD600 !important; }
    .st-rj { color: #FFD600 !important; }
    .st-rk { color: #FFD600 !important; }
    .st-rl { color: #FFD600 !important; }
    .st-rm { color: #FFD600 !important; }
    .st-rn { color: #FFD600 !important; }
    .st-ro { color: #FFD600 !important; }
    .st-rp { color: #FFD600 !important; }
    .st-rq { color: #FFD600 !important; }
    .st-rr { color: #FFD600 !important; }
    .st-rs { color: #FFD600 !important; }
    .st-rt { color: #FFD600 !important; }
    .st-ru { color: #FFD600 !important; }
    .st-rv { color: #FFD600 !important; }
    .st-rw { color: #FFD600 !important; }
    .st-rx { color: #FFD600 !important; }
    .st-ry { color: #FFD600 !important; }
    .st-rz { color: #FFD600 !important; }
    .st-s0 { color: #FFD600 !important; }
    .st-s1 { color: #FFD600 !important; }
    .st-s2 { color: #FFD600 !important; }
    .st-s3 { color: #FFD600 !important; }
    .st-s4 { color: #FFD600 !important; }
    .st-s5 { color: #FFD600 !important; }
    .st-s6 { color: #FFD600 !important; }
    .st-s7 { color: #FFD600 !important; }
    .st-s8 { color: #FFD600 !important; }
    .st-s9 { color: #FFD600 !important; }
    .st-sa { color: #FFD600 !important; }
    .st-sb { color: #FFD600 !important; }
    .st-sc { color: #FFD600 !important; }
    .st-sd { color: #FFD600 !important; }
    .st-se { color: #FFD600 !important; }
    .st-sf { color: #FFD600 !important; }
    .st-sg { color: #FFD600 !important; }
    .st-sh { color: #FFD600 !important; }
    .st-si { color: #FFD600 !important; }
    .st-sj { color: #FFD600 !important; }
    .st-sk { color: #FFD600 !important; }
    .st-sl { color: #FFD600 !important; }
    .st-sm { color: #FFD600 !important; }
    .st-sn { color: #FFD600 !important; }
    .st-so { color: #FFD600 !important; }
    .st-sp { color: #FFD600 !important; }
    .st-sq { color: #FFD600 !important; }
    .st-sr { color: #FFD600 !important; }
    .st-ss { color: #FFD600 !important; }
    .st-st { color: #FFD600 !important; }
    .st-su { color: #FFD600 !important; }
    .st-sv { color: #FFD600 !important; }
    .st-sw { color: #FFD600 !important; }
    .st-sx { color: #FFD600 !important; }
    .st-sy { color: #FFD600 !important; }
    .st-sz { color: #FFD600 !important; }
    .st-t0 { color: #FFD600 !important; }
    .st-t1 { color: #FFD600 !important; }
    .st-t2 { color: #FFD600 !important; }
    .st-t3 { color: #FFD600 !important; }
    .st-t4 { color: #FFD600 !important; }
    .st-t5 { color: #FFD600 !important; }
    .st-t6 { color: #FFD600 !important; }
    .st-t7 { color: #FFD600 !important; }
    .st-t8 { color: #FFD600 !important; }
    .st-t9 { color: #FFD600 !important; }
    .st-ta { color: #FFD600 !important; }
    .st-tb { color: #FFD600 !important; }
    .st-tc { color: #FFD600 !important; }
    .st-td { color: #FFD600 !important; }
    .st-te { color: #FFD600 !important; }
    .st-tf { color: #FFD600 !important; }
    .st-tg { color: #FFD600 !important; }
    .st-th { color: #FFD600 !important; }
    .st-ti { color: #FFD600 !important; }
    .st-tj { color: #FFD600 !important; }
    .st-tk { color: #FFD600 !important; }
    .st-tl { color: #FFD600 !important; }
    .st-tm { color: #FFD600 !important; }
    .st-tn { color: #FFD600 !important; }
    .st-to { color: #FFD600 !important; }
    .st-tp { color: #FFD600 !important; }
    .st-tq { color: #FFD600 !important; }
    .st-tr { color: #FFD600 !important; }
    .st-ts { color: #FFD600 !important; }
    .st-tt { color: #FFD600 !important; }
    .st-tu { color: #FFD600 !important; }
    .st-tv { color: #FFD600 !important; }
    .st-tw { color: #FFD600 !important; }
    .st-tx { color: #FFD600 !important; }
    .st-ty { color: #FFD600 !important; }
    .st-tz { color: #FFD600 !important; }
    .st-u0 { color: #FFD600 !important; }
    .st-u1 { color: #FFD600 !important; }
    .st-u2 { color: #FFD600 !important; }
    .st-u3 { color: #FFD600 !important; }
    .st-u4 { color: #FFD600 !important; }
    .st-u5 { color: #FFD600 !important; }
    .st-u6 { color: #FFD600 !important; }
    .st-u7 { color: #FFD600 !important; }
    .st-u8 { color: #FFD600 !important; }
    .st-u9 { color: #FFD600 !important; }
    .st-ua { color: #FFD600 !important; }
    .st-ub { color: #FFD600 !important; }
    .st-uc { color: #FFD600 !important; }
    .st-ud { color: #FFD600 !important; }
    .st-ue { color: #FFD600 !important; }
    .st-uf { color: #FFD600 !important; }
    .st-ug { color: #FFD600 !important; }
    .st-uh { color: #FFD600 !important; }
    .st-ui { color: #FFD600 !important; }
    .st-uj { color: #FFD600 !important; }
    .st-uk { color: #FFD600 !important; }
    .st-ul { color: #FFD600 !important; }
    .st-um { color: #FFD600 !important; }
    .st-un { color: #FFD600 !important; }
    .st-uo { color: #FFD600 !important; }
    .st-up { color: #FFD600 !important; }
    .st-uq { color: #FFD600 !important; }
    .st-ur { color: #FFD600 !important; }
    .st-us { color: #FFD600 !important; }
    .st-ut { color: #FFD600 !important; }
    .st-uu { color: #FFD600 !important; }
    .st-uv { color: #FFD600 !important; }
    .st-uw { color: #FFD600 !important; }
    .st-ux { color: #FFD600 !important; }
    .st-uy { color: #FFD600 !important; }
    .st-uz { color: #FFD600 !important; }
    .st-v0 { color: #FFD600 !important; }
    .st-v1 { color: #FFD600 !important; }
    .st-v2 { color: #FFD600 !important; }
    .st-v3 { color: #FFD600 !important; }
    .st-v4 { color: #FFD600 !important; }
    .st-v5 { color: #FFD600 !important; }
    .st-v6 { color: #FFD600 !important; }
    .st-v7 { color: #FFD600 !important; }
    .st-v8 { color: #FFD600 !important; }
    .st-v9 { color: #FFD600 !important; }
    .st-va { color: #FFD600 !important; }
    .st-vb { color: #FFD600 !important; }
    .st-vc { color: #FFD600 !important; }
    .st-vd { color: #FFD600 !important; }
    .st-ve { color: #FFD600 !important; }
    .st-vf { color: #FFD600 !important; }
    .st-vg { color: #FFD600 !important; }
    .st-vh { color: #FFD600 !important; }
    .st-vi { color: #FFD600 !important; }
    .st-vj { color: #FFD600 !important; }
    .st-vk { color: #FFD600 !important; }
    .st-vl { color: #FFD600 !important; }
    .st-vm { color: #FFD600 !important; }
    .st-vn { color: #FFD600 !important; }
    .st-vo { color: #FFD600 !important; }
    .st-vp { color: #FFD600 !important; }
    .st-vq { color: #FFD600 !important; }
    .st-vr { color: #FFD600 !important; }
    .st-vs { color: #FFD600 !important; }
    .st-vt { color: #FFD600 !important; }
    .st-vu { color: #FFD600 !important; }
    .st-vv { color: #FFD600 !important; }
    .st-vw { color: #FFD600 !important; }
    .st-vx { color: #FFD600 !important; }
    .st-vy { color: #FFD600 !important; }
    .st-vz { color: #FFD600 !important; }
    .st-w0 { color: #FFD600 !important; }
    .st-w1 { color: #FFD600 !important; }
    .st-w2 { color: #FFD600 !important; }
    .st-w3 { color: #FFD600 !important; }
    .st-w4 { color: #FFD600 !important; }
    .st-w5 { color: #FFD600 !important; }
    .st-w6 { color: #FFD600 !important; }
    .st-w7 { color: #FFD600 !important; }
    .st-w8 { color: #FFD600 !important; }
    .st-w9 { color: #FFD600 !important; }
    .st-wa { color: #FFD600 !important; }
    .st-wb { color: #FFD600 !important; }
    .st-wc { color: #FFD600 !important; }
    .st-wd { color: #FFD600 !important; }
    .st-we { color: #FFD600 !important; }
    .st-wf { color: #FFD600 !important; }
    .st-wg { color: #FFD600 !important; }
    .st-wh { color: #FFD600 !important; }
    .st-wi { color: #FFD600 !important; }
    .st-wj { color: #FFD600 !important; }
    .st-wk { color: #FFD600 !important; }
    .st-wl { color: #FFD600 !important; }
    .st-wm { color: #FFD600 !important; }
    .st-wn { color: #FFD600 !important; }
    .st-wo { color: #FFD600 !important; }
    .st-wp { color: #FFD600 !important; }
    .st-wq { color: #FFD600 !important; }
    .st-wr { color: #FFD600 !important; }
    .st-ws { color: #FFD600 !important; }
    .st-wt { color: #FFD600 !important; }
    .st-wu { color: #FFD600 !important; }
    .st-wv { color: #FFD600 !important; }
    .st-ww { color: #FFD600 !important; }
    .st-wx { color: #FFD600 !important; }
    .st-wy { color: #FFD600 !important; }
    .st-wz { color: #FFD600 !important; }
    .st-x0 { color: #FFD600 !important; }
    .st-x1 { color: #FFD600 !important; }
    .st-x2 { color: #FFD600 !important; }
    .st-x3 { color: #FFD600 !important; }
    .st-x4 { color: #FFD600 !important; }
    .st-x5 { color: #FFD600 !important; }
    .st-x6 { color: #FFD600 !important; }
    .st-x7 { color: #FFD600 !important; }
    .st-x8 { color: #FFD600 !important; }
    .st-x9 { color: #FFD600 !important; }
    .st-xa { color: #FFD600 !important; }
    .st-xb { color: #FFD600 !important; }
    .st-xc { color: #FFD600 !important; }
    .st-xd { color: #FFD600 !important; }
    .st-xe { color: #FFD600 !important; }
    .st-xf { color: #FFD600 !important; }
    .st-xg { color: #FFD600 !important; }
    .st-xh { color: #FFD600 !important; }
    .st-xi { color: #FFD600 !important; }
    .st-xj { color: #FFD600 !important; }
    .st-xk { color: #FFD600 !important; }
    .st-xl { color: #FFD600 !important; }
    .st-xm { color: #FFD600 !important; }
    .st-xn { color: #FFD600 !important; }
    .st-xo { color: #FFD600 !important; }
    .st-xp { color: #FFD600 !important; }
    .st-xq { color: #FFD600 !important; }
    .st-xr { color: #FFD600 !important; }
    .st-xs { color: #FFD600 !important; }
    .st-xt { color: #FFD600 !important; }
    .st-xu { color: #FFD600 !important; }
    .st-xv { color: #FFD600 !important; }
    .st-xw { color: #FFD600 !important; }
    .st-xx { color: #FFD600 !important; }
    .st-xy { color: #FFD600 !important; }
    .st-xz { color: #FFD600 !important; }
    .st-y0 { color: #FFD600 !important; }
    .st-y1 { color: #FFD600 !important; }
    .st-y2 { color: #FFD600 !important; }
    .st-y3 { color: #FFD600 !important; }
    .st-y4 { color: #FFD600 !important; }
    .st-y5 { color: #FFD600 !important; }
    .st-y6 { color: #FFD600 !important; }
    .st-y7 { color: #FFD600 !important; }
    .st-y8 { color: #FFD600 !important; }
    .st-y9 { color: #FFD600 !important; }
    .st-ya { color: #FFD600 !important; }
    .st-yb { color: #FFD600 !important; }
    .st-yc { color: #FFD600 !important; }
    .st-yd { color: #FFD600 !important; }
    .st-ye { color: #FFD600 !important; }
    .st-yf { color: #FFD600 !important; }
    .st-yg { color: #FFD600 !important; }
    .st-yh { color: #FFD600 !important; }
    .st-yi { color: #FFD600 !important; }
    .st-yj { color: #FFD600 !important; }
    .st-yk { color: #FFD600 !important; }
    .st-yl { color: #FFD600 !important; }
    .st-ym { color: #FFD600 !important; }
    .st-yn { color: #FFD600 !important; }
    .st-yo { color: #FFD600 !important; }
    .st-yp { color: #FFD600 !important; }
    .st-yq { color: #FFD600 !important; }
    .st-yr { color: #FFD600 !important; }
    .st-ys { color: #FFD600 !important; }
    .st-yt { color: #FFD600 !important; }
    .st-yu { color: #FFD600 !important; }
    .st-yv { color: #FFD600 !important; }
    .st-yw { color: #FFD600 !important; }
    .st-yx { color: #FFD600 !important; }
    .st-yy { color: #FFD600 !important; }
    .st-yz { color: #FFD600 !important; }
    .st-z0 { color: #FFD600 !important; }
    .st-z1 { color: #FFD600 !important; }
    .st-z2 { color: #FFD600 !important; }
    .st-z3 { color: #FFD600 !important; }
    .st-z4 { color: #FFD600 !important; }
    .st-z5 { color: #FFD600 !important; }
    .st-z6 { color: #FFD600 !important; }
    .st-z7 { color: #FFD600 !important; }
    .st-z8 { color: #FFD600 !important; }
    .st-z9 { color: #FFD600 !important; }
    .st-za { color: #FFD600 !important; }
    .st-zb { color: #FFD600 !important; }
    .st-zc { color: #FFD600 !important; }
    .st-zd { color: #FFD600 !important; }
    .st-ze { color: #FFD600 !important; }
    .st-zf { color: #FFD600 !important; }
    .st-zg { color: #FFD600 !important; }
    .st-zh { color: #FFD600 !important; }
    .st-zi { color: #FFD600 !important; }
    .st-zj { color: #FFD600 !important; }
    .st-zk { color: #FFD600 !important; }
    .st-zl { color: #FFD600 !important; }
    .st-zm { color: #FFD600 !important; }
    .st-zn { color: #FFD600 !important; }
    .st-zo { color: #FFD600 !important; }
    .st-zp { color: #FFD600 !important; }
    .st-zq { color: #FFD600 !important; }
    .st-zr { color: #FFD600 !important; }
    .st-zs { color: #FFD600 !important; }
    .st-zt { color: #FFD600 !important; }
    .st-zu { color: #FFD600 !important; }
    .st-zv { color: #FFD600 !important; }
    .st-zw { color: #FFD600 !important; }
    .st-zx { color: #FFD600 !important; }
    .st-zy { color: #FFD600 !important; }
    .st-zz { color: #FFD600 !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Title ---
st.title("Monte Carlo Wealth Simulator")

# --- Sidebar Inputs ---
st.sidebar.header("Simulation Parameters")
initial_capital = st.sidebar.number_input("Initial Capital ($)", min_value=1000, max_value=1_000_000, value=10000, step=1000)
mu = st.sidebar.slider("Expected Annual Return (%)", min_value=-10.0, max_value=20.0, value=7.0, step=0.1)
sigma = st.sidebar.slider("Annual Volatility (%)", min_value=1.0, max_value=50.0, value=15.0, step=0.1)
n_sim = st.sidebar.slider("Number of Simulations", min_value=100, max_value=5000, value=1000, step=100)
time_horizon = st.sidebar.slider("Time Horizon (Years)", min_value=1, max_value=50, value=30, step=1)

# --- Simulation ---
def simulate_gbm(S0, mu, sigma, T, n_sim, n_steps=252):
    dt = T / n_steps
    mu = mu / 100  # convert to decimal
    sigma = sigma / 100
    drift = (mu - 0.5 * sigma ** 2) * dt
    diffusion = sigma * np.sqrt(dt)
    Z = np.random.randn(n_sim, n_steps)
    increments = drift + diffusion * Z
    log_paths = np.cumsum(increments, axis=1)
    log_paths = np.hstack([np.zeros((n_sim, 1)), log_paths])
    S = S0 * np.exp(log_paths)
    return S

n_steps = 252 * time_horizon
sim_paths = simulate_gbm(initial_capital, mu, sigma, time_horizon, n_sim, n_steps)
times = np.linspace(0, time_horizon, n_steps + 1)

# --- Metrics ---
final_values = sim_paths[:, -1]
mean_final = np.mean(final_values)
worst_final = np.min(final_values)
best_final = np.max(final_values)

# --- Plotting ---
percentile_5 = np.percentile(sim_paths, 5, axis=0)
percentile_95 = np.percentile(sim_paths, 95, axis=0)
mean_path = np.mean(sim_paths, axis=0)

fig = go.Figure()

# All paths (semi-transparent)
for i in range(min(n_sim, 200)):
    fig.add_trace(go.Scatter(
        x=times, y=sim_paths[i],
        mode='lines',
        line=dict(color='rgba(255,255,255,0.07)', width=1),
        showlegend=False,
        hoverinfo='skip'
    ))

# 5th-95th percentile band
fig.add_traces([
    go.Scatter(
        x=times, y=percentile_95,
        line=dict(color='rgba(255,214,0,0.0)'),
        showlegend=False,
        hoverinfo='skip',
        name='95th Percentile',
    ),
    go.Scatter(
        x=times, y=percentile_5,
        fill='tonexty',
        fillcolor='rgba(255,214,0,0.18)',
        line=dict(color='rgba(255,214,0,0.0)'),
        showlegend=False,
        hoverinfo='skip',
        name='5th Percentile',
    )
])

# Mean path
fig.add_trace(go.Scatter(
    x=times, y=mean_path,
    mode='lines',
    line=dict(color='#FFD600', width=3),
    name='Mean Path',
    hoverinfo='skip'
))

# Layout
fig.update_layout(
    template='plotly_dark',
    plot_bgcolor='#18191A',
    paper_bgcolor='#18191A',
    font=dict(color='#FFD600'),
    title="Monte Carlo Simulated Wealth Paths",
    xaxis_title="Years",
    yaxis_title="Portfolio Value ($)",
    showlegend=False,
    margin=dict(l=20, r=20, t=60, b=20),
    hovermode='x unified',
    transition={'duration': 900, 'easing': 'cubic-in-out'}
)

# --- Smooth Appearance Animation ---
fig.update_traces(visible=False)
if st.button("Show Simulation"):
    for i in range(len(fig.data)):
        fig.data[i].visible = True
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Click 'Show Simulation' to display the results.")

# --- Key Metrics ---
st.subheader("Key Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Expected Final Value", f"${mean_final:,.0f}")
col2.metric("Worst Case", f"${worst_final:,.0f}")
col3.metric("Best Case", f"${best_final:,.0f}")

st.caption("""
Monte Carlo simulation using geometric Brownian motion. All values in USD.\n
Yellow band: 5th-95th percentile.\n
Mean path: bright yellow.\n
All paths: white, semi-transparent.\n
No financial advice.\n""")
