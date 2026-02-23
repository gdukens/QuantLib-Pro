import streamlit as st
import numpy as np
import pandas as pd
from scipy.stats import norm, t
import plotly.graph_objects as go

# --- Streamlit Page Config ---
st.set_page_config(
    page_title="3D Tail Risk Distribution Morph Engine",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📈"
)

# --- Dark Theme Styling ---
st.markdown(
    """
    <style>
    body, .stApp { background-color: #18191A; color: #F5F6FA; }
    .st-bb { background: #23272F; }
    .st-cq { color: #F5F6FA; }
    .st-dx { color: #F5F6FA; }
    .st-gd { color: #F5F6FA; }
    .st-gi { color: #F5F6FA; }
    .st-gj { color: #F5F6FA; }
    .st-gk { color: #F5F6FA; }
    .st-gm { color: #F5F6FA; }
    .st-gp { color: #F5F6FA; }
    .st-gq { color: #F5F6FA; }
    .st-gr { color: #F5F6FA; }
    .st-bs { background: #23272F; }
    .st-cq { color: #F5F6FA; }
    .st-cv { color: #F5F6FA; }
    .st-cw { color: #F5F6FA; }
    .st-cx { color: #F5F6FA; }
    .st-cy { color: #F5F6FA; }
    .st-cz { color: #F5F6FA; }
    .st-da { color: #F5F6FA; }
    .st-db { color: #F5F6FA; }
    .st-dc { color: #F5F6FA; }
    .st-dd { color: #F5F6FA; }
    .st-de { color: #F5F6FA; }
    .st-df { color: #F5F6FA; }
    .st-dg { color: #F5F6FA; }
    .st-dh { color: #F5F6FA; }
    .st-di { color: #F5F6FA; }
    .st-dj { color: #F5F6FA; }
    .st-dk { color: #F5F6FA; }
    .st-dl { color: #F5F6FA; }
    .st-dm { color: #F5F6FA; }
    .st-dn { color: #F5F6FA; }
    .st-do { color: #F5F6FA; }
    .st-dp { color: #F5F6FA; }
    .st-dq { color: #F5F6FA; }
    .st-dr { color: #F5F6FA; }
    .st-ds { color: #F5F6FA; }
    .st-dt { color: #F5F6FA; }
    .st-du { color: #F5F6FA; }
    .st-dv { color: #F5F6FA; }
    .st-dw { color: #F5F6FA; }
    .st-dx { color: #F5F6FA; }
    .st-dy { color: #F5F6FA; }
    .st-dz { color: #F5F6FA; }
    .st-e0 { color: #F5F6FA; }
    .st-e1 { color: #F5F6FA; }
    .st-e2 { color: #F5F6FA; }
    .st-e3 { color: #F5F6FA; }
    .st-e4 { color: #F5F6FA; }
    .st-e5 { color: #F5F6FA; }
    .st-e6 { color: #F5F6FA; }
    .st-e7 { color: #F5F6FA; }
    .st-e8 { color: #F5F6FA; }
    .st-e9 { color: #F5F6FA; }
    .st-ea { color: #F5F6FA; }
    .st-eb { color: #F5F6FA; }
    .st-ec { color: #F5F6FA; }
    .st-ed { color: #F5F6FA; }
    .st-ee { color: #F5F6FA; }
    .st-ef { color: #F5F6FA; }
    .st-eg { color: #F5F6FA; }
    .st-eh { color: #F5F6FA; }
    .st-ei { color: #F5F6FA; }
    .st-ej { color: #F5F6FA; }
    .st-ek { color: #F5F6FA; }
    .st-el { color: #F5F6FA; }
    .st-em { color: #F5F6FA; }
    .st-en { color: #F5F6FA; }
    .st-eo { color: #F5F6FA; }
    .st-ep { color: #F5F6FA; }
    .st-eq { color: #F5F6FA; }
    .st-er { color: #F5F6FA; }
    .st-es { color: #F5F6FA; }
    .st-et { color: #F5F6FA; }
    .st-eu { color: #F5F6FA; }
    .st-ev { color: #F5F6FA; }
    .st-ew { color: #F5F6FA; }
    .st-ex { color: #F5F6FA; }
    .st-ey { color: #F5F6FA; }
    .st-ez { color: #F5F6FA; }
    .st-f0 { color: #F5F6FA; }
    .st-f1 { color: #F5F6FA; }
    .st-f2 { color: #F5F6FA; }
    .st-f3 { color: #F5F6FA; }
    .st-f4 { color: #F5F6FA; }
    .st-f5 { color: #F5F6FA; }
    .st-f6 { color: #F5F6FA; }
    .st-f7 { color: #F5F6FA; }
    .st-f8 { color: #F5F6FA; }
    .st-f9 { color: #F5F6FA; }
    .st-fa { color: #F5F6FA; }
    .st-fb { color: #F5F6FA; }
    .st-fc { color: #F5F6FA; }
    .st-fd { color: #F5F6FA; }
    .st-fe { color: #F5F6FA; }
    .st-ff { color: #F5F6FA; }
    .st-fg { color: #F5F6FA; }
    .st-fh { color: #F5F6FA; }
    .st-fi { color: #F5F6FA; }
    .st-fj { color: #F5F6FA; }
    .st-fk { color: #F5F6FA; }
    .st-fl { color: #F5F6FA; }
    .st-fm { color: #F5F6FA; }
    .st-fn { color: #F5F6FA; }
    .st-fo { color: #F5F6FA; }
    .st-fp { color: #F5F6FA; }
    .st-fq { color: #F5F6FA; }
    .st-fr { color: #F5F6FA; }
    .st-fs { color: #F5F6FA; }
    .st-ft { color: #F5F6FA; }
    .st-fu { color: #F5F6FA; }
    .st-fv { color: #F5F6FA; }
    .st-fw { color: #F5F6FA; }
    .st-fx { color: #F5F6FA; }
    .st-fy { color: #F5F6FA; }
    .st-fz { color: #F5F6FA; }
    .st-g0 { color: #F5F6FA; }
    .st-g1 { color: #F5F6FA; }
    .st-g2 { color: #F5F6FA; }
    .st-g3 { color: #F5F6FA; }
    .st-g4 { color: #F5F6FA; }
    .st-g5 { color: #F5F6FA; }
    .st-g6 { color: #F5F6FA; }
    .st-g7 { color: #F5F6FA; }
    .st-g8 { color: #F5F6FA; }
    .st-g9 { color: #F5F6FA; }
    .st-ga { color: #F5F6FA; }
    .st-gb { color: #F5F6FA; }
    .st-gc { color: #F5F6FA; }
    .st-gd { color: #F5F6FA; }
    .st-ge { color: #F5F6FA; }
    .st-gf { color: #F5F6FA; }
    .st-gg { color: #F5F6FA; }
    .st-gh { color: #F5F6FA; }
    .st-gi { color: #F5F6FA; }
    .st-gj { color: #F5F6FA; }
    .st-gk { color: #F5F6FA; }
    .st-gl { color: #F5F6FA; }
    .st-gm { color: #F5F6FA; }
    .st-gn { color: #F5F6FA; }
    .st-go { color: #F5F6FA; }
    .st-gp { color: #F5F6FA; }
    .st-gq { color: #F5F6FA; }
    .st-gr { color: #F5F6FA; }
    .st-gs { color: #F5F6FA; }
    .st-gt { color: #F5F6FA; }
    .st-gu { color: #F5F6FA; }
    .st-gv { color: #F5F6FA; }
    .st-gw { color: #F5F6FA; }
    .st-gx { color: #F5F6FA; }
    .st-gy { color: #F5F6FA; }
    .st-gz { color: #F5F6FA; }
    .st-h0 { color: #F5F6FA; }
    .st-h1 { color: #F5F6FA; }
    .st-h2 { color: #F5F6FA; }
    .st-h3 { color: #F5F6FA; }
    .st-h4 { color: #F5F6FA; }
    .st-h5 { color: #F5F6FA; }
    .st-h6 { color: #F5F6FA; }
    .st-h7 { color: #F5F6FA; }
    .st-h8 { color: #F5F6FA; }
    .st-h9 { color: #F5F6FA; }
    .st-ha { color: #F5F6FA; }
    .st-hb { color: #F5F6FA; }
    .st-hc { color: #F5F6FA; }
    .st-hd { color: #F5F6FA; }
    .st-he { color: #F5F6FA; }
    .st-hf { color: #F5F6FA; }
    .st-hg { color: #F5F6FA; }
    .st-hh { color: #F5F6FA; }
    .st-hi { color: #F5F6FA; }
    .st-hj { color: #F5F6FA; }
    .st-hk { color: #F5F6FA; }
    .st-hl { color: #F5F6FA; }
    .st-hm { color: #F5F6FA; }
    .st-hn { color: #F5F6FA; }
    .st-ho { color: #F5F6FA; }
    .st-hp { color: #F5F6FA; }
    .st-hq { color: #F5F6FA; }
    .st-hr { color: #F5F6FA; }
    .st-hs { color: #F5F6FA; }
    .st-ht { color: #F5F6FA; }
    .st-hu { color: #F5F6FA; }
    .st-hv { color: #F5F6FA; }
    .st-hw { color: #F5F6FA; }
    .st-hx { color: #F5F6FA; }
    .st-hy { color: #F5F6FA; }
    .st-hz { color: #F5F6FA; }
    .st-i0 { color: #F5F6FA; }
    .st-i1 { color: #F5F6FA; }
    .st-i2 { color: #F5F6FA; }
    .st-i3 { color: #F5F6FA; }
    .st-i4 { color: #F5F6FA; }
    .st-i5 { color: #F5F6FA; }
    .st-i6 { color: #F5F6FA; }
    .st-i7 { color: #F5F6FA; }
    .st-i8 { color: #F5F6FA; }
    .st-i9 { color: #F5F6FA; }
    .st-ia { color: #F5F6FA; }
    .st-ib { color: #F5F6FA; }
    .st-ic { color: #F5F6FA; }
    .st-id { color: #F5F6FA; }
    .st-ie { color: #F5F6FA; }
    .st-if { color: #F5F6FA; }
    .st-ig { color: #F5F6FA; }
    .st-ih { color: #F5F6FA; }
    .st-ii { color: #F5F6FA; }
    .st-ij { color: #F5F6FA; }
    .st-ik { color: #F5F6FA; }
    .st-il { color: #F5F6FA; }
    .st-im { color: #F5F6FA; }
    .st-in { color: #F5F6FA; }
    .st-io { color: #F5F6FA; }
    .st-ip { color: #F5F6FA; }
    .st-iq { color: #F5F6FA; }
    .st-ir { color: #F5F6FA; }
    .st-is { color: #F5F6FA; }
    .st-it { color: #F5F6FA; }
    .st-iu { color: #F5F6FA; }
    .st-iv { color: #F5F6FA; }
    .st-iw { color: #F5F6FA; }
    .st-ix { color: #F5F6FA; }
    .st-iy { color: #F5F6FA; }
    .st-iz { color: #F5F6FA; }
    .st-j0 { color: #F5F6FA; }
    .st-j1 { color: #F5F6FA; }
    .st-j2 { color: #F5F6FA; }
    .st-j3 { color: #F5F6FA; }
    .st-j4 { color: #F5F6FA; }
    .st-j5 { color: #F5F6FA; }
    .st-j6 { color: #F5F6FA; }
    .st-j7 { color: #F5F6FA; }
    .st-j8 { color: #F5F6FA; }
    .st-j9 { color: #F5F6FA; }
    .st-ja { color: #F5F6FA; }
    .st-jb { color: #F5F6FA; }
    .st-jc { color: #F5F6FA; }
    .st-jd { color: #F5F6FA; }
    .st-je { color: #F5F6FA; }
    .st-jf { color: #F5F6FA; }
    .st-jg { color: #F5F6FA; }
    .st-jh { color: #F5F6FA; }
    .st-ji { color: #F5F6FA; }
    .st-jj { color: #F5F6FA; }
    .st-jk { color: #F5F6FA; }
    .st-jl { color: #F5F6FA; }
    .st-jm { color: #F5F6FA; }
    .st-jn { color: #F5F6FA; }
    .st-jo { color: #F5F6FA; }
    .st-jp { color: #F5F6FA; }
    .st-jq { color: #F5F6FA; }
    .st-jr { color: #F5F6FA; }
    .st-js { color: #F5F6FA; }
    .st-jt { color: #F5F6FA; }
    .st-ju { color: #F5F6FA; }
    .st-jv { color: #F5F6FA; }
    .st-jw { color: #F5F6FA; }
    .st-jx { color: #F5F6FA; }
    .st-jy { color: #F5F6FA; }
    .st-jz { color: #F5F6FA; }
    .st-k0 { color: #F5F6FA; }
    .st-k1 { color: #F5F6FA; }
    .st-k2 { color: #F5F6FA; }
    .st-k3 { color: #F5F6FA; }
    .st-k4 { color: #F5F6FA; }
    .st-k5 { color: #F5F6FA; }
    .st-k6 { color: #F5F6FA; }
    .st-k7 { color: #F5F6FA; }
    .st-k8 { color: #F5F6FA; }
    .st-k9 { color: #F5F6FA; }
    .st-ka { color: #F5F6FA; }
    .st-kb { color: #F5F6FA; }
    .st-kc { color: #F5F6FA; }
    .st-kd { color: #F5F6FA; }
    .st-ke { color: #F5F6FA; }
    .st-kf { color: #F5F6FA; }
    .st-kg { color: #F5F6FA; }
    .st-kh { color: #F5F6FA; }
    .st-ki { color: #F5F6FA; }
    .st-kj { color: #F5F6FA; }
    .st-kk { color: #F5F6FA; }
    .st-kl { color: #F5F6FA; }
    .st-km { color: #F5F6FA; }
    .st-kn { color: #F5F6FA; }
    .st-ko { color: #F5F6FA; }
    .st-kp { color: #F5F6FA; }
    .st-kq { color: #F5F6FA; }
    .st-kr { color: #F5F6FA; }
    .st-ks { color: #F5F6FA; }
    .st-kt { color: #F5F6FA; }
    .st-ku { color: #F5F6FA; }
    .st-kv { color: #F5F6FA; }
    .st-kw { color: #F5F6FA; }
    .st-kx { color: #F5F6FA; }
    .st-ky { color: #F5F6FA; }
    .st-kz { color: #F5F6FA; }
    .st-l0 { color: #F5F6FA; }
    .st-l1 { color: #F5F6FA; }
    .st-l2 { color: #F5F6FA; }
    .st-l3 { color: #F5F6FA; }
    .st-l4 { color: #F5F6FA; }
    .st-l5 { color: #F5F6FA; }
    .st-l6 { color: #F5F6FA; }
    .st-l7 { color: #F5F6FA; }
    .st-l8 { color: #F5F6FA; }
    .st-l9 { color: #F5F6FA; }
    .st-la { color: #F5F6FA; }
    .st-lb { color: #F5F6FA; }
    .st-lc { color: #F5F6FA; }
    .st-ld { color: #F5F6FA; }
    .st-le { color: #F5F6FA; }
    .st-lf { color: #F5F6FA; }
    .st-lg { color: #F5F6FA; }
    .st-lh { color: #F5F6FA; }
    .st-li { color: #F5F6FA; }
    .st-lj { color: #F5F6FA; }
    .st-lk { color: #F5F6FA; }
    .st-ll { color: #F5F6FA; }
    .st-lm { color: #F5F6FA; }
    .st-ln { color: #F5F6FA; }
    .st-lo { color: #F5F6FA; }
    .st-lp { color: #F5F6FA; }
    .st-lq { color: #F5F6FA; }
    .st-lr { color: #F5F6FA; }
    .st-ls { color: #F5F6FA; }
    .st-lt { color: #F5F6FA; }
    .st-lu { color: #F5F6FA; }
    .st-lv { color: #F5F6FA; }
    .st-lw { color: #F5F6FA; }
    .st-lx { color: #F5F6FA; }
    .st-ly { color: #F5F6FA; }
    .st-lz { color: #F5F6FA; }
    .st-m0 { color: #F5F6FA; }
    .st-m1 { color: #F5F6FA; }
    .st-m2 { color: #F5F6FA; }
    .st-m3 { color: #F5F6FA; }
    .st-m4 { color: #F5F6FA; }
    .st-m5 { color: #F5F6FA; }
    .st-m6 { color: #F5F6FA; }
    .st-m7 { color: #F5F6FA; }
    .st-m8 { color: #F5F6FA; }
    .st-m9 { color: #F5F6FA; }
    .st-ma { color: #F5F6FA; }
    .st-mb { color: #F5F6FA; }
    .st-mc { color: #F5F6FA; }
    .st-md { color: #F5F6FA; }
    .st-me { color: #F5F6FA; }
    .st-mf { color: #F5F6FA; }
    .st-mg { color: #F5F6FA; }
    .st-mh { color: #F5F6FA; }
    .st-mi { color: #F5F6FA; }
    .st-mj { color: #F5F6FA; }
    .st-mk { color: #F5F6FA; }
    .st-ml { color: #F5F6FA; }
    .st-mm { color: #F5F6FA; }
    .st-mn { color: #F5F6FA; }
    .st-mo { color: #F5F6FA; }
    .st-mp { color: #F5F6FA; }
    .st-mq { color: #F5F6FA; }
    .st-mr { color: #F5F6FA; }
    .st-ms { color: #F5F6FA; }
    .st-mt { color: #F5F6FA; }
    .st-mu { color: #F5F6FA; }
    .st-mv { color: #F5F6FA; }
    .st-mw { color: #F5F6FA; }
    .st-mx { color: #F5F6FA; }
    .st-my { color: #F5F6FA; }
    .st-mz { color: #F5F6FA; }
    .st-n0 { color: #F5F6FA; }
    .st-n1 { color: #F5F6FA; }
    .st-n2 { color: #F5F6FA; }
    .st-n3 { color: #F5F6FA; }
    .st-n4 { color: #F5F6FA; }
    .st-n5 { color: #F5F6FA; }
    .st-n6 { color: #F5F6FA; }
    .st-n7 { color: #F5F6FA; }
    .st-n8 { color: #F5F6FA; }
    .st-n9 { color: #F5F6FA; }
    .st-na { color: #F5F6FA; }
    .st-nb { color: #F5F6FA; }
    .st-nc { color: #F5F6FA; }
    .st-nd { color: #F5F6FA; }
    .st-ne { color: #F5F6FA; }
    .st-nf { color: #F5F6FA; }
    .st-ng { color: #F5F6FA; }
    .st-nh { color: #F5F6FA; }
    .st-ni { color: #F5F6FA; }
    .st-nj { color: #F5F6FA; }
    .st-nk { color: #F5F6FA; }
    .st-nl { color: #F5F6FA; }
    .st-nm { color: #F5F6FA; }
    .st-nn { color: #F5F6FA; }
    .st-no { color: #F5F6FA; }
    .st-np { color: #F5F6FA; }
    .st-nq { color: #F5F6FA; }
    .st-nr { color: #F5F6FA; }
    .st-ns { color: #F5F6FA; }
    .st-nt { color: #F5F6FA; }
    .st-nu { color: #F5F6FA; }
    .st-nv { color: #F5F6FA; }
    .st-nw { color: #F5F6FA; }
    .st-nx { color: #F5F6FA; }
    .st-ny { color: #F5F6FA; }
    .st-nz { color: #F5F6FA; }
    .st-o0 { color: #F5F6FA; }
    .st-o1 { color: #F5F6FA; }
    .st-o2 { color: #F5F6FA; }
    .st-o3 { color: #F5F6FA; }
    .st-o4 { color: #F5F6FA; }
    .st-o5 { color: #F5F6FA; }
    .st-o6 { color: #F5F6FA; }
    .st-o7 { color: #F5F6FA; }
    .st-o8 { color: #F5F6FA; }
    .st-o9 { color: #F5F6FA; }
    .st-oa { color: #F5F6FA; }
    .st-ob { color: #F5F6FA; }
    .st-oc { color: #F5F6FA; }
    .st-od { color: #F5F6FA; }
    .st-oe { color: #F5F6FA; }
    .st-of { color: #F5F6FA; }
    .st-og { color: #F5F6FA; }
    .st-oh { color: #F5F6FA; }
    .st-oi { color: #F5F6FA; }
    .st-oj { color: #F5F6FA; }
    .st-ok { color: #F5F6FA; }
    .st-ol { color: #F5F6FA; }
    .st-om { color: #F5F6FA; }
    .st-on { color: #F5F6FA; }
    .st-oo { color: #F5F6FA; }
    .st-op { color: #F5F6FA; }
    .st-oq { color: #F5F6FA; }
    .st-or { color: #F5F6FA; }
    .st-os { color: #F5F6FA; }
    .st-ot { color: #F5F6FA; }
    .st-ou { color: #F5F6FA; }
    .st-ov { color: #F5F6FA; }
    .st-ow { color: #F5F6FA; }
    .st-ox { color: #F5F6FA; }
    .st-oy { color: #F5F6FA; }
    .st-oz { color: #F5F6FA; }
    .st-p0 { color: #F5F6FA; }
    .st-p1 { color: #F5F6FA; }
    .st-p2 { color: #F5F6FA; }
    .st-p3 { color: #F5F6FA; }
    .st-p4 { color: #F5F6FA; }
    .st-p5 { color: #F5F6FA; }
    .st-p6 { color: #F5F6FA; }
    .st-p7 { color: #F5F6FA; }
    .st-p8 { color: #F5F6FA; }
    .st-p9 { color: #F5F6FA; }
    .st-pa { color: #F5F6FA; }
    .st-pb { color: #F5F6FA; }
    .st-pc { color: #F5F6FA; }
    .st-pd { color: #F5F6FA; }
    .st-pe { color: #F5F6FA; }
    .st-pf { color: #F5F6FA; }
    .st-pg { color: #F5F6FA; }
    .st-ph { color: #F5F6FA; }
    .st-pi { color: #F5F6FA; }
    .st-pj { color: #F5F6FA; }
    .st-pk { color: #F5F6FA; }
    .st-pl { color: #F5F6FA; }
    .st-pm { color: #F5F6FA; }
    .st-pn { color: #F5F6FA; }
    .st-po { color: #F5F6FA; }
    .st-pp { color: #F5F6FA; }
    .st-pq { color: #F5F6FA; }
    .st-pr { color: #F5F6FA; }
    .st-ps { color: #F5F6FA; }
    .st-pt { color: #F5F6FA; }
    .st-pu { color: #F5F6FA; }
    .st-pv { color: #F5F6FA; }
    .st-pw { color: #F5F6FA; }
    .st-px { color: #F5F6FA; }
    .st-py { color: #F5F6FA; }
    .st-pz { color: #F5F6FA; }
    .st-q0 { color: #F5F6FA; }
    .st-q1 { color: #F5F6FA; }
    .st-q2 { color: #F5F6FA; }
    .st-q3 { color: #F5F6FA; }
    .st-q4 { color: #F5F6FA; }
    .st-q5 { color: #F5F6FA; }
    .st-q6 { color: #F5F6FA; }
    .st-q7 { color: #F5F6FA; }
    .st-q8 { color: #F5F6FA; }
    .st-q9 { color: #F5F6FA; }
    .st-qa { color: #F5F6FA; }
    .st-qb { color: #F5F6FA; }
    .st-qc { color: #F5F6FA; }
    .st-qd { color: #F5F6FA; }
    .st-qe { color: #F5F6FA; }
    .st-qf { color: #F5F6FA; }
    .st-qg { color: #F5F6FA; }
    .st-qh { color: #F5F6FA; }
    .st-qi { color: #F5F6FA; }
    .st-qj { color: #F5F6FA; }
    .st-qk { color: #F5F6FA; }
    .st-ql { color: #F5F6FA; }
    .st-qm { color: #F5F6FA; }
    .st-qn { color: #F5F6FA; }
    .st-qo { color: #F5F6FA; }
    .st-qp { color: #F5F6FA; }
    .st-qq { color: #F5F6FA; }
    .st-qr { color: #F5F6FA; }
    .st-qs { color: #F5F6FA; }
    .st-qt { color: #F5F6FA; }
    .st-qu { color: #F5F6FA; }
    .st-qv { color: #F5F6FA; }
    .st-qw { color: #F5F6FA; }
    .st-qx { color: #F5F6FA; }
    .st-qy { color: #F5F6FA; }
    .st-qz { color: #F5F6FA; }
    .st-r0 { color: #F5F6FA; }
    .st-r1 { color: #F5F6FA; }
    .st-r2 { color: #F5F6FA; }
    .st-r3 { color: #F5F6FA; }
    .st-r4 { color: #F5F6FA; }
    .st-r5 { color: #F5F6FA; }
    .st-r6 { color: #F5F6FA; }
    .st-r7 { color: #F5F6FA; }
    .st-r8 { color: #F5F6FA; }
    .st-r9 { color: #F5F6FA; }
    .st-ra { color: #F5F6FA; }
    .st-rb { color: #F5F6FA; }
    .st-rc { color: #F5F6FA; }
    .st-rd { color: #F5F6FA; }
    .st-re { color: #F5F6FA; }
    .st-rf { color: #F5F6FA; }
    .st-rg { color: #F5F6FA; }
    .st-rh { color: #F5F6FA; }
    .st-ri { color: #F5F6FA; }
    .st-rj { color: #F5F6FA; }
    .st-rk { color: #F5F6FA; }
    .st-rl { color: #F5F6FA; }
    .st-rm { color: #F5F6FA; }
    .st-rn { color: #F5F6FA; }
    .st-ro { color: #F5F6FA; }
    .st-rp { color: #F5F6FA; }
    .st-rq { color: #F5F6FA; }
    .st-rr { color: #F5F6FA; }
    .st-rs { color: #F5F6FA; }
    .st-rt { color: #F5F6FA; }
    .st-ru { color: #F5F6FA; }
    .st-rv { color: #F5F6FA; }
    .st-rw { color: #F5F6FA; }
    .st-rx { color: #F5F6FA; }
    .st-ry { color: #F5F6FA; }
    .st-rz { color: #F5F6FA; }
    .st-s0 { color: #F5F6FA; }
    .st-s1 { color: #F5F6FA; }
    .st-s2 { color: #F5F6FA; }
    .st-s3 { color: #F5F6FA; }
    .st-s4 { color: #F5F6FA; }
    .st-s5 { color: #F5F6FA; }
    .st-s6 { color: #F5F6FA; }
    .st-s7 { color: #F5F6FA; }
    .st-s8 { color: #F5F6FA; }
    .st-s9 { color: #F5F6FA; }
    .st-sa { color: #F5F6FA; }
    .st-sb { color: #F5F6FA; }
    .st-sc { color: #F5F6FA; }
    .st-sd { color: #F5F6FA; }
    .st-se { color: #F5F6FA; }
    .st-sf { color: #F5F6FA; }
    .st-sg { color: #F5F6FA; }
    .st-sh { color: #F5F6FA; }
    .st-si { color: #F5F6FA; }
    .st-sj { color: #F5F6FA; }
    .st-sk { color: #F5F6FA; }
    .st-sl { color: #F5F6FA; }
    .st-sm { color: #F5F6FA; }
    .st-sn { color: #F5F6FA; }
    .st-so { color: #F5F6FA; }
    .st-sp { color: #F5F6FA; }
    .st-sq { color: #F5F6FA; }
    .st-sr { color: #F5F6FA; }
    .st-ss { color: #F5F6FA; }
    .st-st { color: #F5F6FA; }
    .st-su { color: #F5F6FA; }
    .st-sv { color: #F5F6FA; }
    .st-sw { color: #F5F6FA; }
    .st-sx { color: #F5F6FA; }
    .st-sy { color: #F5F6FA; }
    .st-sz { color: #F5F6FA; }
    .st-t0 { color: #F5F6FA; }
    .st-t1 { color: #F5F6FA; }
    .st-t2 { color: #F5F6FA; }
    .st-t3 { color: #F5F6FA; }
    .st-t4 { color: #F5F6FA; }
    .st-t5 { color: #F5F6FA; }
    .st-t6 { color: #F5F6FA; }
    .st-t7 { color: #F5F6FA; }
    .st-t8 { color: #F5F6FA; }
    .st-t9 { color: #F5F6FA; }
    .st-ta { color: #F5F6FA; }
    .st-tb { color: #F5F6FA; }
    .st-tc { color: #F5F6FA; }
    .st-td { color: #F5F6FA; }
    .st-te { color: #F5F6FA; }
    .st-tf { color: #F5F6FA; }
    .st-tg { color: #F5F6FA; }
    .st-th { color: #F5F6FA; }
    .st-ti { color: #F5F6FA; }
    .st-tj { color: #F5F6FA; }
    .st-tk { color: #F5F6FA; }
    .st-tl { color: #F5F6FA; }
    .st-tm { color: #F5F6FA; }
    .st-tn { color: #F5F6FA; }
    .st-to { color: #F5F6FA; }
    .st-tp { color: #F5F6FA; }
    .st-tq { color: #F5F6FA; }
    .st-tr { color: #F5F6FA; }
    .st-ts { color: #F5F6FA; }
    .st-tt { color: #F5F6FA; }
    .st-tu { color: #F5F6FA; }
    .st-tv { color: #F5F6FA; }
    .st-tw { color: #F5F6FA; }
    .st-tx { color: #F5F6FA; }
    .st-ty { color: #F5F6FA; }
    .st-tz { color: #F5F6FA; }
    .st-u0 { color: #F5F6FA; }
    .st-u1 { color: #F5F6FA; }
    .st-u2 { color: #F5F6FA; }
    .st-u3 { color: #F5F6FA; }
    .st-u4 { color: #F5F6FA; }
    .st-u5 { color: #F5F6FA; }
    .st-u6 { color: #F5F6FA; }
    .st-u7 { color: #F5F6FA; }
    .st-u8 { color: #F5F6FA; }
    .st-u9 { color: #F5F6FA; }
    .st-ua { color: #F5F6FA; }
    .st-ub { color: #F5F6FA; }
    .st-uc { color: #F5F6FA; }
    .st-ud { color: #F5F6FA; }
    .st-ue { color: #F5F6FA; }
    .st-uf { color: #F5F6FA; }
    .st-ug { color: #F5F6FA; }
    .st-uh { color: #F5F6FA; }
    .st-ui { color: #F5F6FA; }
    .st-uj { color: #F5F6FA; }
    .st-uk { color: #F5F6FA; }
    .st-ul { color: #F5F6FA; }
    .st-um { color: #F5F6FA; }
    .st-un { color: #F5F6FA; }
    .st-uo { color: #F5F6FA; }
    .st-up { color: #F5F6FA; }
    .st-uq { color: #F5F6FA; }
    .st-ur { color: #F5F6FA; }
    .st-us { color: #F5F6FA; }
    .st-ut { color: #F5F6FA; }
    .st-uu { color: #F5F6FA; }
    .st-uv { color: #F5F6FA; }
    .st-uw { color: #F5F6FA; }
    .st-ux { color: #F5F6FA; }
    .st-uy { color: #F5F6FA; }
    .st-uz { color: #F5F6FA; }
    .st-v0 { color: #F5F6FA; }
    .st-v1 { color: #F5F6FA; }
    .st-v2 { color: #F5F6FA; }
    .st-v3 { color: #F5F6FA; }
    .st-v4 { color: #F5F6FA; }
    .st-v5 { color: #F5F6FA; }
    .st-v6 { color: #F5F6FA; }
    .st-v7 { color: #F5F6FA; }
    .st-v8 { color: #F5F6FA; }
    .st-v9 { color: #F5F6FA; }
    .st-va { color: #F5F6FA; }
    .st-vb { color: #F5F6FA; }
    .st-vc { color: #F5F6FA; }
    .st-vd { color: #F5F6FA; }
    .st-ve { color: #F5F6FA; }
    .st-vf { color: #F5F6FA; }
    .st-vg { color: #F5F6FA; }
    .st-vh { color: #F5F6FA; }
    .st-vi { color: #F5F6FA; }
    .st-vj { color: #F5F6FA; }
    .st-vk { color: #F5F6FA; }
    .st-vl { color: #F5F6FA; }
    .st-vm { color: #F5F6FA; }
    .st-vn { color: #F5F6FA; }
    .st-vo { color: #F5F6FA; }
    .st-vp { color: #F5F6FA; }
    .st-vq { color: #F5F6FA; }
    .st-vr { color: #F5F6FA; }
    .st-vs { color: #F5F6FA; }
    .st-vt { color: #F5F6FA; }
    .st-vu { color: #F5F6FA; }
    .st-vv { color: #F5F6FA; }
    .st-vw { color: #F5F6FA; }
    .st-vx { color: #F5F6FA; }
    .st-vy { color: #F5F6FA; }
    .st-vz { color: #F5F6FA; }
    .st-w0 { color: #F5F6FA; }
    .st-w1 { color: #F5F6FA; }
    .st-w2 { color: #F5F6FA; }
    .st-w3 { color: #F5F6FA; }
    .st-w4 { color: #F5F6FA; }
    .st-w5 { color: #F5F6FA; }
    .st-w6 { color: #F5F6FA; }
    .st-w7 { color: #F5F6FA; }
    .st-w8 { color: #F5F6FA; }
    .st-w9 { color: #F5F6FA; }
    .st-wa { color: #F5F6FA; }
    .st-wb { color: #F5F6FA; }
    .st-wc { color: #F5F6FA; }
    .st-wd { color: #F5F6FA; }
    .st-we { color: #F5F6FA; }
    .st-wf { color: #F5F6FA; }
    .st-wg { color: #F5F6FA; }
    .st-wh { color: #F5F6FA; }
    .st-wi { color: #F5F6FA; }
    .st-wj { color: #F5F6FA; }
    .st-wk { color: #F5F6FA; }
    .st-wl { color: #F5F6FA; }
    .st-wm { color: #F5F6FA; }
    .st-wn { color: #F5F6FA; }
    .st-wo { color: #F5F6FA; }
    .st-wp { color: #F5F6FA; }
    .st-wq { color: #F5F6FA; }
    .st-wr { color: #F5F6FA; }
    .st-ws { color: #F5F6FA; }
    .st-wt { color: #F5F6FA; }
    .st-wu { color: #F5F6FA; }
    .st-wv { color: #F5F6FA; }
    .st-ww { color: #F5F6FA; }
    .st-wx { color: #F5F6FA; }
    .st-wy { color: #F5F6FA; }
    .st-wz { color: #F5F6FA; }
    .st-x0 { color: #F5F6FA; }
    .st-x1 { color: #F5F6FA; }
    .st-x2 { color: #F5F6FA; }
    .st-x3 { color: #F5F6FA; }
    .st-x4 { color: #F5F6FA; }
    .st-x5 { color: #F5F6FA; }
    .st-x6 { color: #F5F6FA; }
    .st-x7 { color: #F5F6FA; }
    .st-x8 { color: #F5F6FA; }
    .st-x9 { color: #F5F6FA; }
    .st-xa { color: #F5F6FA; }
    .st-xb { color: #F5F6FA; }
    .st-xc { color: #F5F6FA; }
    .st-xd { color: #F5F6FA; }
    .st-xe { color: #F5F6FA; }
    .st-xf { color: #F5F6FA; }
    .st-xg { color: #F5F6FA; }
    .st-xh { color: #F5F6FA; }
    .st-xi { color: #F5F6FA; }
    .st-xj { color: #F5F6FA; }
    .st-xk { color: #F5F6FA; }
    .st-xl { color: #F5F6FA; }
    .st-xm { color: #F5F6FA; }
    .st-xn { color: #F5F6FA; }
    .st-xo { color: #F5F6FA; }
    .st-xp { color: #F5F6FA; }
    .st-xq { color: #F5F6FA; }
    .st-xr { color: #F5F6FA; }
    .st-xs { color: #F5F6FA; }
    .st-xt { color: #F5F6FA; }
    .st-xu { color: #F5F6FA; }
    .st-xv { color: #F5F6FA; }
    .st-xw { color: #F5F6FA; }
    .st-xx { color: #F5F6FA; }
    .st-xy { color: #F5F6FA; }
    .st-xz { color: #F5F6FA; }
    .st-y0 { color: #F5F6FA; }
    .st-y1 { color: #F5F6FA; }
    .st-y2 { color: #F5F6FA; }
    .st-y3 { color: #F5F6FA; }
    .st-y4 { color: #F5F6FA; }
    .st-y5 { color: #F5F6FA; }
    .st-y6 { color: #F5F6FA; }
    .st-y7 { color: #F5F6FA; }
    .st-y8 { color: #F5F6FA; }
    .st-y9 { color: #F5F6FA; }
    .st-ya { color: #F5F6FA; }
    .st-yb { color: #F5F6FA; }
    .st-yc { color: #F5F6FA; }
    .st-yd { color: #F5F6FA; }
    .st-ye { color: #F5F6FA; }
    .st-yf { color: #F5F6FA; }
    .st-yg { color: #F5F6FA; }
    .st-yh { color: #F5F6FA; }
    .st-yi { color: #F5F6FA; }
    .st-yj { color: #F5F6FA; }
    .st-yk { color: #F5F6FA; }
    .st-yl { color: #F5F6FA; }
    .st-ym { color: #F5F6FA; }
    .st-yn { color: #F5F6FA; }
    .st-yo { color: #F5F6FA; }
    .st-yp { color: #F5F6FA; }
    .st-yq { color: #F5F6FA; }
    .st-yr { color: #F5F6FA; }
    .st-ys { color: #F5F6FA; }
    .st-yt { color: #F5F6FA; }
    .st-yu { color: #F5F6FA; }
    .st-yv { color: #F5F6FA; }
    .st-yw { color: #F5F6FA; }
    .st-yx { color: #F5F6FA; }
    .st-yy { color: #F5F6FA; }
    .st-yz { color: #F5F6FA; }
    .st-z0 { color: #F5F6FA; }
    .st-z1 { color: #F5F6FA; }
    .st-z2 { color: #F5F6FA; }
    .st-z3 { color: #F5F6FA; }
    .st-z4 { color: #F5F6FA; }
    .st-z5 { color: #F5F6FA; }
    .st-z6 { color: #F5F6FA; }
    .st-z7 { color: #F5F6FA; }
    .st-z8 { color: #F5F6FA; }
    .st-z9 { color: #F5F6FA; }
    .st-za { color: #F5F6FA; }
    .st-zb { color: #F5F6FA; }
    .st-zc { color: #F5F6FA; }
    .st-zd { color: #F5F6FA; }
    .st-ze { color: #F5F6FA; }
    .st-zf { color: #F5F6FA; }
    .st-zg { color: #F5F6FA; }
    .st-zh { color: #F5F6FA; }
    .st-zi { color: #F5F6FA; }
    .st-zj { color: #F5F6FA; }
    .st-zk { color: #F5F6FA; }
    .st-zl { color: #F5F6FA; }
    .st-zm { color: #F5F6FA; }
    .st-zn { color: #F5F6FA; }
    .st-zo { color: #F5F6FA; }
    .st-zp { color: #F5F6FA; }
    .st-zq { color: #F5F6FA; }
    .st-zr { color: #F5F6FA; }
    .st-zs { color: #F5F6FA; }
    .st-zt { color: #F5F6FA; }
    .st-zu { color: #F5F6FA; }
    .st-zv { color: #F5F6FA; }
    .st-zw { color: #F5F6FA; }
    .st-zx { color: #F5F6FA; }
    .st-zy { color: #F5F6FA; }
    .st-zz { color: #F5F6FA; }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Sidebar Controls ---
st.sidebar.title("3D Tail Risk Distribution Morph Engine")
st.sidebar.markdown("---")
df_min = 2.1
df_max = 30
df_default = 8
vol_min = 0.01
vol_max = 0.2
vol_default = 0.05
stress_min = 1.0
stress_max = 5.0
stress_default = 1.0
time_min = 10
time_max = 50
time_default = 25

user_df = st.sidebar.slider(
    "Student-t Degrees of Freedom (Tail Weight)",
    min_value=float(df_min),
    max_value=float(df_max),
    value=float(df_default),
    step=0.1
)
user_vol = st.sidebar.slider(
    "Volatility (Std Dev, Annualized)",
    min_value=float(vol_min),
    max_value=float(vol_max),
    value=float(vol_default),
    step=0.01
)
user_stress = st.sidebar.slider(
    "Stress Multiplier (Tail Stress)",
    min_value=float(stress_min),
    max_value=float(stress_max),
    value=float(stress_default),
    step=0.05
)
time_steps = st.sidebar.slider(
    "Time Horizon Steps",
    min_value=int(time_min),
    max_value=int(time_max),
    value=int(time_default),
    step=1
)

# --- Core Functions ---
def generate_distribution(x, t_idx, n_steps, base_vol, base_df, stress_mult):
    # Morphing: alpha goes 0 (Gaussian) to 1 (Student-t) as t_idx increases
    alpha = t_idx / (n_steps - 1)
    # Interpolate df: from inf (Gaussian) to user df (Student-t)
    morph_df = (1 - alpha) * 1e6 + alpha * base_df
    # Interpolate volatility: stress increases volatility
    morph_vol = base_vol * (1 + alpha * (stress_mult - 1))
    # Gaussian for large df, Student-t for low df
    if morph_df > 1000:
        pdf = norm.pdf(x, loc=0, scale=morph_vol)
    else:
        pdf = t.pdf(x / morph_vol, df=morph_df) / morph_vol
    # Clamp extreme densities for numerical stability
    pdf = np.clip(pdf, 1e-12, 1e2)
    return pdf, morph_df, morph_vol

def compute_tail_metrics(x, pdf, alpha=0.05):
    # PDF to CDF
    dx = x[1] - x[0]
    cdf = np.cumsum(pdf) * dx
    cdf = np.clip(cdf, 0, 1)
    # Find VaR (quantile)
    try:
        var_idx = np.where(cdf >= alpha)[0][0]
    except IndexError:
        var_idx = 0
    var = x[var_idx]
    # Expected Shortfall: mean of losses worse than VaR
    es = np.sum(pdf[x <= var] * x[x <= var]) / np.sum(pdf[x <= var]) if np.sum(pdf[x <= var]) > 0 else var
    return var, es

def build_3d_surface(x, time_grid, z_grid, var_grid=None):
    fig = go.Figure()
    # 3D surface
    fig.add_trace(go.Surface(
        x=x,
        y=time_grid,
        z=z_grid,
        colorscale="Viridis",
        showscale=True,
        opacity=0.95,
        name="Density Surface"
    ))
    # VaR overlay (as a line)
    if var_grid is not None:
        fig.add_trace(go.Scatter3d(
            x=var_grid,
            y=time_grid,
            z=[np.interp(v, x, z) for v, z in zip(var_grid, z_grid)],
            mode="lines",
            line=dict(color="red", width=6),
            name="VaR (5%)"
        ))
    fig.update_layout(
        title="3D Tail Risk Distribution Morph Engine",
        scene=dict(
            xaxis_title="Return Magnitude",
            yaxis_title="Time Step",
            zaxis_title="Probability Density",
            xaxis=dict(backgroundcolor="#18191A", color="#F5F6FA"),
            yaxis=dict(backgroundcolor="#18191A", color="#F5F6FA"),
            zaxis=dict(backgroundcolor="#18191A", color="#F5F6FA"),
        ),
        margin=dict(l=10, r=10, b=10, t=40),
        paper_bgcolor="#18191A",
        plot_bgcolor="#18191A",
        font=dict(color="#F5F6FA", size=14),
        legend=dict(bgcolor="#23272F", font=dict(color="#F5F6FA")),
        height=700
    )
    return fig

# --- Main Simulation ---
# X grid: returns
x = np.linspace(-0.2, 0.2, 400)
# Time grid
time_grid = np.arange(time_steps)
z_grid = np.zeros((time_steps, len(x)))
var_grid = np.zeros(time_steps)
es_grid = np.zeros(time_steps)
df_grid = np.zeros(time_steps)
vol_grid = np.zeros(time_steps)

for t_idx in range(time_steps):
    pdf, morph_df, morph_vol = generate_distribution(x, t_idx, time_steps, user_vol, user_df, user_stress)
    z_grid[t_idx, :] = pdf
    var, es = compute_tail_metrics(x, pdf, alpha=0.05)
    var_grid[t_idx] = var
    es_grid[t_idx] = es
    df_grid[t_idx] = morph_df
    vol_grid[t_idx] = morph_vol

# --- Metrics Display ---
st.title("3D Tail Risk Distribution Morph Engine")
st.markdown("""
#### Simulates the morphing of a returns distribution from Gaussian to heavy-tailed Student-t under stress. 
- **X-axis:** Return magnitude
- **Y-axis:** Time (stress progression)
- **Z-axis:** Probability density
""")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Final VaR (5%)", f"{var_grid[-1]:.4f}")
col2.metric("Final Expected Shortfall (ES)", f"{es_grid[-1]:.4f}")
col3.metric("Final Volatility", f"{vol_grid[-1]:.4f}")
col4.metric("Final Degrees of Freedom", f"{df_grid[-1]:.2f}")

# --- 3D Surface Plot ---
fig = build_3d_surface(x, time_grid, z_grid, var_grid=var_grid)
st.plotly_chart(fig, use_container_width=True)

# --- Data Table (Optional) ---
with st.expander("Show Tail Metrics Table"):
    df_metrics = pd.DataFrame({
        "Time Step": time_grid,
        "VaR (5%)": var_grid,
        "Expected Shortfall": es_grid,
        "Volatility": vol_grid,
        "Degrees of Freedom": df_grid
    })
    st.dataframe(df_metrics, use_container_width=True)
